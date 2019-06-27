import logging
from distributed import Worker
from tornado.ioloop import IOLoop

scheduler_address = "192.168.10.123"
scheduler_port = 8786
death_time_out = 30

scheduler = "%s:%s" % (scheduler_address, scheduler_port)

worker = Worker(scheduler, death_timeout=death_time_out)

worker.start()

loop = IOLoop.current()
loop.start()

logging.info("Exiting the Dask Worker normally")
