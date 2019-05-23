import logging
import signal

import traceback, signal, sys


def debug_sighandler(sig, frame):
    """
    Interrupt running process, and provide a python prompt for
    interactive debugging.
    """
    d = {'_frame': frame}  # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    logging.info("-------------------\n")
    logging.info("Signal received : traceback for main thread:\n")
    logging.info(''.join(traceback.format_stack(frame)))
    logging.info("Additional threads\n")
    for f2 in sys._current_frames().values():
        logging.info("STACK:")
        logging.info(''.join(traceback.format_stack(f2)))
        logging.info("\n")
    logging.info("-------------------\n")
    sys.stdout.flush()
    sys.stderr.flush()


def setup_log_signal_handling():
    """



    :return:
    """
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] [%(process)s/%(threadName)s] [%(levelname)s] [%(name)s] %(message)s')
    logging.info("setup_log() called")
    logging.info("Installing debugging signal handler")
    signal.signal(signal.SIGUSR1, debug_sighandler)
