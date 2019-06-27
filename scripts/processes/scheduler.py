from distributed import Scheduler
from distributed.bokeh.scheduler import BokehScheduler
from tornado.ioloop import IOLoop

services = {('bokeh', 8787): (BokehScheduler, {'prefix': None})}

scheduler = Scheduler(services=services)

scheduler.start('tcp://:8786')

loop = IOLoop.current()
loop.start()
