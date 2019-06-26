import logging
import socket
import time
from threading import Thread

from dask import delayed
from distributed import Client
from distributed import Scheduler
from distributed.bokeh.scheduler import BokehScheduler
from joblib import Parallel
from joblib import parallel_backend
from joblib import register_parallel_backend
from joblib._dask import DaskDistributedBackend
from tornado.ioloop import IOLoop

from utils import setup_log_signal_handling


def dummy_task():
    return 0


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

    n_jobs = 4
    verbose = 100
    backend = "dask"

    register_parallel_backend(backend, DaskDistributedBackend)

    joblib_parallel = Parallel(n_jobs=n_jobs, verbose=verbose, pre_dispatch="n_jobs", backend=backend)
    logging.info("Entering Dask Context")
    with parallel_backend("dask"):
        logging.info("Entered Dask Context")
        logging.info("Running 'dummy_task' with %s jobs and %s as a parallel back-end" % (n_jobs, backend))

        results = joblib_parallel(delayed(dummy_task)(i for i in range(100000000)))

        logging.info("Done running 'fit_and_score_estimator'")
        logging.info("Exiting Dask context")

    logging.info("Exited Dask context")
    logging.info("Done")
