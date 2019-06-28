# Minimal Reproducible Bug Example: dead lock in `Parallel` when using `dask` as a back-end

## 🚧 Work in progress

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

Jobs generally hang or crash and `joblib.Parallel` does not return, blocking the main process.

For now, I can't reproduce the initial problem exactly, several other problems
arise.

**Exploration and diagnostic**:

To better have an understanding of what's going on, logs have been added on branches based respectively on:
 - [`jjerphan/distributed 1.28.0`](https://github.com/jjerphan/distributed/pull/2) for logs on `1.28.0` for `distributed`
 - [`jjerphan/joblib 0.13.2`](https://github.com/jjerphan/joblib/pull/1) for logs on `0.13.2` for `joblib`

See the following issue:
[`joblib/issues/875`](https://github.com/joblib/joblib/issues/875) fo
explanation.

**Recap of problems:**

Here is a recap of logs of different problem I had on different setup:
 - Hanging on `Client._update_scheduler_info` after submission to `Parallel.__call__`
    - commit:[3f3fb9b708b5ec74607c3edb5fb32f7fac9eeea1](https://github.com/jjerphan/joblib_dask_deadlock/tree/3f3fb9b708b5ec74607c3edb5fb32f7fac9eeea1)
    - [gist](https://gist.github.com/jjerphan/018908beb8422d7c81fb00198f5fd9f7)
 - Hanging on `Scheduler.handle_task_finished`:
    - recap: tasks are run on `Workers`, results come back to `Scheduler`, the connection between those two `Servers` can't be closed
    - commit: [95a34d6bdfd3cbf8f491bab70f02a384feb1cc95](https://github.com/jjerphan/joblib_dask_deadlock/tree/95a34d6bdfd3cbf8f491bab70f02a384feb1cc95)
    - [gist](https://gist.github.com/jjerphan/9bf4eb3a33e26813067a6aa95b0f484c)
    
## Reproduce using Kubernetes

Clone this repo:
```bash
git clone git@github.com:jjerphan/joblib_dask_deadlock.git
cd joblib_dask_deadlock
```

Eventually checkout to the different commit listed above.

A simple helm chart has been developed to reproduce the setup and the errors easily.

### ⚠️⚠️⚠️ Warning: I don't tag [the image used](https://cloud.docker.com/u/jjerphan/repository/docker/jjerphan/joblib_dask_deadlock) as I am currently inspecting the problem. So you might want to fork this repo and adapt it by publishing your own image.

You can do this building the image locally and pushing it on Docker Hub:

```bash
docker build -t yourself/joblib_dask_deadlock:latest .
docker push yourself/joblib_dask_deadlock:latest
```

Then you will need to edit [`chart/values.yaml`](./chart/values.yaml) by replacing `jjerphan/joblib_dask_deadlock` by `yourself/joblib_dask_deadlock`.

You can start the infrastructure by running:
```bash
helm install  ./chart --name joblib-dask-deadlock-test
```

Latter you can the infrastructure by running:

```bash
helm del --purge joblib-dask-deadlock-test
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

> **TODO:** not tested but should work, else **ask me**

In different terminal, run

```bash
python scripts/entrypoint.py server
python scripts/entrypoint.py worker
```
