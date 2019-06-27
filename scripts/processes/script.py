import logging

from distributed import Client
from joblib import Parallel
from joblib import delayed
from joblib import parallel_backend
from joblib import register_parallel_backend
from joblib._dask import DaskDistributedBackend


def dummy_task(i):
    return i

logger = logging.getLogger('server')
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] [%(process)s/%(threadName)s] [%(levelname)s] [%(name)s] %(message)s')

logging.info("Started reproducible example")
logging.info("Creating Dask Client")

scheduler_ip = "192.168.10.123"
scheduler_port = 8786
scheduler_address_port = "%s:%s" % (scheduler_ip, scheduler_port)
dask_client = Client(scheduler_address_port)
logging.info("Created Dask Client")

n_jobs = 4
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
