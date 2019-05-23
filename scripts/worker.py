# encoding: utf-8
"""
Executor for containerized execution of dask worker
"""
import logging
import os
import signal
import platform
from threading import Thread
from time import sleep

import dask
import distributed
from distributed import Worker
from tornado.ioloop import IOLoop

from scripts.utils import setup_log_signal_handling

logger = logging.getLogger('dask_worker')


if __name__ == "__main__":
    setup_log_signal_handling()

    scheduler_address = os.getenv('DASK_SCHEDULER_ADDRESS')
    scheduler_port = os.getenv('DASK_SCHEDULER_PORT', 8687)
    death_time_out = 30

    scheduler = "%s:%s" % (scheduler_address, scheduler_port)

    worker = Worker(scheduler, death_timeout=death_time_out)

    pid = os.getpid()

    def worker_watchdog():
        """
        A routine that watches the state of the Worker
        that is spawned and that kills it when possible.

        This is used to resolve a teardown problem when
        the connection between the Scheduler and the Worker
        ends.

        :return:
        """
        delay = 5  # seconds

        while True:
            sleep(delay)
            logging.info("Dask Worker status : %s" % worker.status)
            if worker.status in ('closing', 'closed'):
                logging.info("Exiting the Dask Worker via watchdog using SIGKILL")
                os.kill(pid, signal.SIGKILL)

    worker_watchdog_thread = Thread(target=worker_watchdog)
    # We activate the daemon explicitly so that this thread
    # is stopped when the main process exits.
    # see: https://docs.python.org/2/library/threading.html#threading.Thread.daemon
    worker_watchdog_thread.daemon = True

    logging.info("Launching Dask Worker via Python API")
    logging.info("Python      version:")
    logging.info(platform.sys.version)
    logging.info("Dask        version: %s" % dask.__version__)
    logging.info("Distributed version: %s" % distributed.__version__)
    worker.start()

    logging.info("Launching Worker Watchdog Thread")
    worker_watchdog_thread.start()

    loop = IOLoop.current()
    loop.start()

    logging.info("Exiting the Dask Worker normally")
