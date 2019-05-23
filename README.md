# Minimal Reproducible Bug Example: dead lock in `joblib.Parallel._lock` when using `dask` as a back-end

## Overview

**tl;dr** : aims at reproducing a dead lock when using `joblib.Parallel` with `dask` as a back-end.

**Context**:

The context is a bit cumbersome:
 - **Dask-wise**: a Client, a Server, 3 Worker
 - **Task executed**: a simple GridSearchCV (2 points) on a `RandomForest`
 - **Process architecture**: subprocesses that are run in containers
    - container are used to run jobs on Kubernetes Clusters typically
    - those process start with an execution of `entrypoint.py` (see [`DockerFile`](./Dockerfile))
    - a subprocess is spawn from this process and run based on the argument given: 
        - `server.py` a process that:
            - spawns the `Scheduler` in a Thread 
            - spawns the `Client` in the main thread 
            - defines the task to run in a joblib context in the main thread
        - `worker.py` that spawns a worker that connect to the `Scheduler`


**Problem**:

Jobs generally hang or crash.

**Exploration and diagnostic**:

To better have an understanding of what's going on, logs have been added on branches based respectively on:
 - [`jjerphan/distributed 1.28.0`]() for logs on `1.28.0` for `distributed`
 - [`jjerphan/joblib 0.13.2`]() for logs on `0.13.2` for `joblib`

See the following issue: [`joblib/issues/875`](https://github.com/joblib/joblib/issues/875) for explanation.

> More to come !

## Reproduce using Kubernetes

Clone this repo:
```bash
git clone git@github.com:jjerphan/mbr_lock.git
cd mbr_lock
```

A simple helm chart has been developed to reproduce the setup and the errors easily.

To do so just run:
```bash
helm install  ./chart --name joblib-dask-deadlock-test
```

### Inspect logs

Just use this to get access to the logs.
```bash
tools/logs | tee logs
```

You can also use the two others scripts to better have an understanding of logs
```bash
tools/count_logs logs
tools/lock_logs logs
```

## Manual setup

A [`DockerFile`](./Dockerfile) defines the entire setup but to try to reproduce it without containerisation here
are some instructions.

### Getting forks

You can have access to forks by cloning the following repositories and installing them as dependencies then.

```bash
# Distributed clone
git clone git@github.com:jjerphan/distributed.git
cd distributed
git checkout 1.28.0_debug
cd ..

# Joblib clone
git clone git@github.com:jjerphan/joblib.git
cd joblib
git checkout 0.13.2_debug
cd ..
```

### Python venv

```bash
python -m venv .venv
source ./venv/bin/activate
```

Install via requirements:

```bash
pip install -r requirements.txt
```

I recommend directly pulling dependencies and installing with the forks:
```bash
pip install -r requirements.txt
pip install -e ./joblib
pip install -e ./distributed
```

### Run

> TODO: not tested but should work, else fix env variables accordingly

In different terminal, run

```bash
python scripts/entrypoint.py server
python scripts/entrypoint.py worker
```