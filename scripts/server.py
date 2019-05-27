import inspect
import logging
import numbers
import socket
import threading
import time
from copy import deepcopy
from itertools import product
from threading import Thread

import scipy
from dask import delayed
from joblib import parallel_backend, Parallel, register_parallel_backend
from joblib._dask import DaskDistributedBackend
from sklearn import clone, metrics
from sklearn.datasets import make_regression
from sklearn.ensemble import RandomForestRegressor
from distributed import Client, Scheduler
from distributed.bokeh.scheduler import BokehScheduler
from sklearn.model_selection import KFold
from sklearn.utils import safe_indexing
from sklearn.utils.metaestimators import _safe_split
from sklearn.utils.validation import _is_arraylike, _num_samples
from tornado.ioloop import IOLoop

from utils import setup_log_signal_handling


class Results:
    """ Just a wrapper. """

    def __init__(self, parameters, test_score, train_score, score_time, fit_time, num_samples):
        self._parameters = parameters
        self._test_score = test_score
        self._train_score = train_score
        self._score_time = score_time
        self._fit_time = fit_time
        self._num_samples = num_samples


class ParametersGenerator(object):
    """ Generate hyper-parameters point on a grid. """

    def __init__(self, param_grid):
        """
        :param param_grid: dict of values or list of values, for eg {'a': [1, 3, 4, 5], 'b': [True, False], 'c': 1}
        """

        # Turning single values into lists
        for k in param_grid.keys():
            if not isinstance(param_grid[k], tuple) and not isinstance(param_grid[k], list):
                param_grid[k] = [param_grid[k]]

        # Sort the dictionary to have a canonical representation of the grid
        param_grid = {key: param_grid[key] for key in sorted(param_grid)}
        for k, p in param_grid.items():
            param_grid[k] = sorted(param_grid[k])

        # Construct the grid
        cartesian_product = product(*param_grid.values())

        params_keys = param_grid.keys()

        # Iterable of dicts, for eg [{'a': 1, 'b': True, 'c': 1}, {'a': 1, 'b': False, 'c': 1}, ...]
        self.named_cartesian_product = list(map(lambda params_values: dict(zip(params_keys, params_values)),
                                            cartesian_product))

    def __len__(self):
        """Number of points on the grid."""
        return len(self.named_cartesian_product)

    def __getitem__(self, index):
        return self.named_cartesian_product[index]


def parameters_folds_generator(nb_folds, X, y, param_grid):
    """
    Return set of parameters and indices for folds.

    :return:
    """

    # Used to generate indices
    folder = KFold(n_splits=nb_folds, shuffle=True, random_state=42)

    parameters_generator = ParametersGenerator(param_grid)

    for parameters in parameters_generator:
        for train_indices, test_indices in folder.split(X, y):
            yield parameters, train_indices, test_indices


def fit_and_score_estimator(estimator, X, y, scorer, parameters, train, test, fit_params):
    """
    Custom function to fit and score a given estimator.

    :param estimator: scikit-learn BaseEstimator interface
    :param X: an array-like, 2 axes
    :param y: an array-like, 2 axes
    :param scorer: a function
    :param parameters: dict
    :param train: an array-like, 1 axe
    :param test: an array-like, 1 axe
    :param fit_params: dict
    :return:
    """

    def index_params(X, v, indices):

        if not _is_arraylike(v) or _num_samples(v) != _num_samples(X):
            # pass through: skip indexing
            return v
        if scipy.sparse.issparse(v):
            v = v.tocsr()
        return safe_indexing(v, indices)

    logging.info("Entering fit_and_score_estimator")

    current_thread = threading.current_thread()
    current_thread.name = "fit_and_score_estimator-%s" % current_thread.ident

    if parameters is not None:
        estimator.set_params(**parameters)

    start_time = time.time()

    X_train, y_train = _safe_split(estimator, X, y, train)
    X_test, y_test = _safe_split(estimator, X, y, test, train)

    # Adjust length of sample weights
    fit_params = fit_params if fit_params is not None else {}

    fit_params = dict([(k, index_params(X, v, train)) for k, v in fit_params.items()])

    # Even with the specific handling done before (the registration back-end and the
    # specification of joblib.Parallel tasks), Dask is used.
    # Here we enforce the usage of a local back-end to remove this problem.
    with parallel_backend("threading"):
        if y_train is None:
            estimator.fit(X_train, **fit_params)
        else:
            estimator.fit(X_train, y_train, **fit_params)

        fit_time = time.time() - start_time

        def score(estimator, X_test, y_test, scorer, indices=None):
            """
            Custom function to score.

            :param estimator: scikit-learn BaseEstimator interface
            :param X_test: an array-like, 2 axes
            :param y_test: an array-like, 2 axes
            :param scorer: a function
            :param indices: an array-like, 1 axe
            :return:
            """
            if y_test is None:
                # Clustering
                score = scorer(estimator, X_test)
            else:
                # Prediction
                if inspect.isfunction(scorer):
                    argspec = inspect.getargspec(scorer)
                else:
                    argspec = [[]]  # scorers are callables, ie. classes

                if 'indices' in argspec[0]:  # regular args
                    score = scorer(estimator, X_test, y_test, indices=indices)
                else:
                    score = scorer(estimator, X_test, y_test)
            if hasattr(score, 'item'):
                try:
                    score = score.item()
                except ValueError:
                    # non-scalar?
                    pass
            if not isinstance(score, numbers.Number):
                raise ValueError("scoring must return a number, got %s (%s) instead."
                                 % (str(score), type(score)))
            return score

        test_score = score(estimator, X_test, y_test, scorer, indices=test)
        train_score = score(estimator, X_train, y_train, scorer, indices=train)
        score_time = time.time() - start_time - fit_time

    end_msg = "Done: fit_time=%.1fs score_time=%.1fs test_score=%s" % (fit_time, score_time, test_score)
    logging.info(end_msg)
    num_samples = _num_samples(X_test)

    return Results(parameters=parameters,
                   test_score=test_score,
                   train_score=train_score,
                   score_time=score_time,
                   fit_time=fit_time,
                   num_samples=num_samples)


if __name__ == "__main__":
    setup_log_signal_handling()

    logger = logging.getLogger('server')
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] [%(process)s/%(threadName)s] [%(levelname)s] [%(name)s] %(message)s')

    logging.info("Started reproducible example")
    scheduler_port = 8786

    def start_dask_scheduler():
        """
        Start the Scheduler in this subprocess.

        Context: A Dask Client is started in the doctor server and needs
        to connect to the Dask Scheduler

        :return:
        """
        services = {('bokeh', 8787): (BokehScheduler, {'prefix': None})}

        scheduler = Scheduler(services=services)

        scheduler_location = 'tcp://:%s' % scheduler_port
        scheduler.start(scheduler_location)

        # Tornado IOLoops are a way for Schedulers, Workers and Clients to communicate.
        # Here, we get the IOLoop of the process and start it.
        # It is used by the Scheduler to communicate with Workers from the outside.
        loop = IOLoop.current()
        loop.start()


    dask_scheduler_thread = Thread(target=start_dask_scheduler)

    # We need to activate the daemon explicitly here so that
    # the thread dedicated to the Scheduler is stopped when
    # the main process exits.
    # see: https://docs.python.org/2/library/threading.html#threading.Thread.daemon
    dask_scheduler_thread.daemon = True

    logging.info("Dask Scheduler: starting on port %s" % scheduler_port)
    dask_scheduler_thread.start()
    logging.info("Dask Scheduler: started on port %s" % scheduler_port)

    logging.info("Creating Dask Client")
    scheduler_ip = socket.gethostbyname(socket.gethostname())
    scheduler_address_port = "%s:%s" % (scheduler_ip, scheduler_port)
    dask_client = Client(scheduler_address_port)
    logging.info("Created Dask Client")

    logging.info("Waiting for Workers to connect")
    time.sleep(5)

    # TODO: Generate a similar dataset
    X, y = make_regression(n_samples=4898,
                           n_features=11,
                           n_informative=11,
                           n_targets=1,
                           bias=0.0,
                           random_state=42)

    estimator = RandomForestRegressor()

    param_grid = {
        'bootstrap': [True],
        'max_depth': [10],
        'min_samples_leaf': [1, 2],
        'min_samples_split': [2],
        'n_estimators': [200]
    }

    # TODO : fix values appropriately
    n_jobs = 4
    nb_folds = 3
    verbose = 100
    backend = "dask"
    fit_params = {}
    scorer = metrics.f1_score

    register_parallel_backend(backend, DaskDistributedBackend)

    joblib_parallel = Parallel(n_jobs=n_jobs, verbose=verbose, pre_dispatch="n_jobs", backend=backend)
    logging.info("Entering Dask Context")
    with parallel_backend("dask"):
        logging.info("Entered Dask Context")

        logging.info("Running 'fit_and_score_estimator' with %s jobs and %s as a parallel back-end" %
                     (n_jobs, backend))
        results = joblib_parallel(
            delayed(fit_and_score_estimator)(estimator=clone(estimator),
                                             X=X,
                                             y=y,
                                             scorer=scorer,
                                             parameters=parameters,
                                             train_indices=train_indices,
                                             test_indices=test_indices,
                                             fit_params=deepcopy(fit_params))
            for parameters, train_indices, test_indices
            in parameters_folds_generator(nb_folds, X, y, param_grid))

        logging.info("Done running 'fit_and_score_estimator'")

        logging.info("Exiting Dask context")

    logging.info("Exited Dask context")

    logging.info("Done")
