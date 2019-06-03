import logging
import socket
import time
from threading import Thread

from distributed import Client
from distributed import Scheduler
from distributed.bokeh.scheduler import BokehScheduler
from joblib import parallel_backend
from joblib import register_parallel_backend
from joblib._dask import DaskDistributedBackend
from sklearn.datasets import make_regression
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeRegressor
from tornado.ioloop import IOLoop

from utils import setup_log_signal_handling

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
    time.sleep(10)

    X, y = make_regression(n_samples=4898,
                           n_features=11,
                           n_informative=11,
                           n_targets=1,
                           bias=0.0,
                           random_state=42)

    estimator = DecisionTreeRegressor()

    param_grid = {
        'max_depth': [10],
        'min_samples_leaf': [1, 2],
        'min_samples_split': [2],
    }

    # TODO : fix values appropriately
    n_jobs = 1
    nb_folds = 3
    verbose = 100
    backend = "dask"
    fit_params = {}
    scorer = "r2"

    register_parallel_backend(backend, DaskDistributedBackend)

    gs_estimator = GridSearchCV(estimator=estimator, param_grid=param_grid)

    logging.info("Entering Dask Context")
    with parallel_backend("dask", scatter=[X, y]):
        logging.info("Entered Dask Context")

        logging.info("Running GridSearchCV.fit with %s as a parallel back-end" % backend)

        gs_estimator.fit(X, y)

        logging.info("Done running GridSearchCV.fit")

        logging.info("Exiting Dask context")

    logging.info("Exited Dask context")

    logging.info("Done")
