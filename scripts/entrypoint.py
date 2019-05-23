import logging
import os
import subprocess
import sys


if __name__ == "__main__":

    # Determining if running a Worker or a Scheduler
    to_launch = sys.argv[1]

    assert to_launch in {"server", "worker"}

    logging.info("Launching a %s" % to_launch)

    # Starting via a system call to manage different python version
    command = "python %s.py" % to_launch

    return_code = subprocess.call(command, shell=True, env=dict(os.environ, LC_ALL='en_US.utf8'))

    # Handles return code
    if os.WIFEXITED(return_code):
        status = "exited with status"
        return_code = os.WEXITSTATUS(return_code)
    elif os.WIFSTOPPED(return_code):
        status = "stopped by signal"
        return_code = os.WSTOPSIG(return_code)
    elif os.WIFSIGNALED(return_code):
        status = "terminated by signal"
        return_code = os.WTERMSIG(return_code)
    else:
        status = "Finished with code"

    status = "Containerized process %s %d" % (status, return_code)

    if return_code == 0:
        logging.info(status)
    else:
        logging.error(status)
