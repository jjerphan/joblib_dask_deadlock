import logging
import os
import platform
import socket
import time
from threading import Thread

import dask
import distributed
from dask import delayed
from distributed import Client
from distributed import Scheduler
from distributed import Worker
from distributed.bokeh.scheduler import BokehScheduler
from joblib import Parallel
from joblib import parallel_backend
from joblib import register_parallel_backend
from joblib._dask import DaskDistributedBackend
from tornado.ioloop import IOLoop

from utils import setup_log_signal_handling


def dummy_task(i):
    """
    Just a dummy task to submit to Dask.

    :return:
    """
    return 0


if __name__ == "__main__":
    setup_log_signal_handling()

    logger = logging.getLogger('server')
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] [%(process)s/%(threadName)s] [%(levelname)s] [%(name)s] %(message)s')

    logging.info("Started reproducible example")
    logging.info("Python      version:")
    logging.info(platform.sys.version)
    logging.info("Dask        version: %s" % dask.__version__)
    logging.info("Distributed version: %s" % distributed.__version__)

    scheduler_port = 8786

    scheduler_ip = socket.gethostbyname('localhost')
    logging.info("Scheduler IP %s" % scheduler_ip)
    scheduler_address_port = "%s:%s" % (scheduler_ip, scheduler_port)

    def start_dask_scheduler():
        """
        Start the Scheduler in this subprocess.

        :return:
        """
        services = {('bokeh', 8787): (BokehScheduler, {'prefix': None})}
        scheduler = Scheduler(services=services)
        scheduler.start(scheduler_address_port)
        loop = IOLoop.current()
        loop.start()

    def start_dask_worker():
        """
        Start a Dask Worker in this subprocess.

        :return:
        """
        death_time_out = 30
        worker = Worker(scheduler_address_port, death_timeout=death_time_out)
        worker.start()
        loop = IOLoop.current()
        loop.start()

    dask_scheduler_thread = Thread(target=start_dask_scheduler)

    # We need to activate the daemon explicitly here so that the thread dedicated to the Scheduler is stopped when
    # the main process exits.
    # see: https://docs.python.org/2/library/threading.html#threading.Thread.daemon
    dask_scheduler_thread.daemon = True

    logging.info("Dask Scheduler: starting on port %s" % scheduler_port)
    dask_scheduler_thread.start()
    logging.info("Dask Scheduler: started on port %s" % scheduler_port)

    n_workers = 1
    worker_threads = list()
    for n in range(n_workers):
        wt = Thread(target=start_dask_worker)
        wt.daemon = True
        logging.info("Dask Worker: starting")
        wt.start()
        logging.info("Dask Worker: started")
        worker_threads.append(wt)

    logging.info("Creating Dask Client")
    dask_client = Client(scheduler_address_port)
    logging.info("Created Dask Client")

    n_jobs = 1
    verbose = 100
    backend = "dask"

    register_parallel_backend(backend, DaskDistributedBackend)

    joblib_parallel = Parallel(n_jobs=n_jobs, verbose=verbose, pre_dispatch="n_jobs", backend=backend)
    logging.info("Entering Dask Context")
    with parallel_backend("dask"):
        logging.info("Entered Dask Context")
        logging.info("Running 'dummy_task' with %s jobs and %s as a parallel back-end" % (n_jobs, backend))

        results = joblib_parallel(delayed(dummy_task)(i) for i in range(1))

        logging.info("Done running 'dummy_task'")
        logging.info("Exiting Dask context")

    logging.info("Exited Dask context")
    logging.info("Done")
