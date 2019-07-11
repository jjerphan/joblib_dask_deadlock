import logging
import logging

import socket
import time
from joblib import parallel_backend
from sklearn.datasets import make_regression
from dask_ml.model_selection import GridSearchCV as DaskGridSearchCV
from sklearn.tree import DecisionTreeRegressor
from threading import Thread
from tornado.ioloop import IOLoop
from utils import setup_log_signal_handling

from distributed import Client
from distributed import Scheduler
from distributed.bokeh.scheduler import BokehScheduler

if __name__ == "__main__":

    # Logging setup
    setup_log_signal_handling()

    logger = logging.getLogger('server')
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] [%(process)s/%(threadName)s] [%(levelname)s] [%(name)s] %(message)s')

    logging.info("Started Server")

    # Scheduler setup
    scheduler_port = 8786
    services = {('bokeh', 8787): (BokehScheduler, {'prefix': None})}
    scheduler = Scheduler(services=services)

    scheduler_location = 'tcp://:%s' % scheduler_port
    scheduler.start(scheduler_location)

    # Tornado IOLoops are a way for Schedulers, Workers and Clients to communicate.
    # Here, we get the IOLoop of the process and start it.
    # It is used by the Scheduler to communicate with Workers from the outside.
    loop = IOLoop.current()

    dask_scheduler_io_loop_thread = Thread(target=loop.start)

    # We need to activate the daemon explicitly here so that
    # the thread dedicated to the Scheduler is stopped when
    # the main process exits.
    # see: https://docs.python.org/2/library/threading.html#threading.Thread.daemon
    dask_scheduler_io_loop_thread.daemon = True

    logging.info("Dask Scheduler: starting on port %s" % scheduler_port)
    dask_scheduler_io_loop_thread.start()
    logging.info("Dask Scheduler: started on port %s" % scheduler_port)

    logging.info("Creating Dask Client")
    scheduler_ip = socket.gethostbyname(socket.gethostname())
    scheduler_address_port = "%s:%s" % (scheduler_ip, scheduler_port)
    dask_client = Client(scheduler_address_port)
    logging.info("Created Dask Client")

    logging.info("Waiting for Workers to connect")
    time.sleep(30)
    logging.info("Done waiting for Workers to connect")

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

    gs_estimator = DaskGridSearchCV(estimator=estimator, param_grid=param_grid)

    logging.info("Entering Dask Context")
    with parallel_backend("dask"):
        logging.info("Entered Dask Context")

        logging.info("Running dask_ml.model_selection.GridSearchCV.fit")
        gs_estimator.fit(X, y)
        logging.info("Done running dask_ml.model_selection.GridSearchCV.fit")

        logging.info("Exiting Dask context")

    logging.info("Exited Dask context")

    logging.info("Done")
