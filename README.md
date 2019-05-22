# Minimal Reproducible Bug Example: dead lock in `joblib.Parallel._lock` when using `dask` as a back-end

## Overview

This repository aims at reproducing a dead lock when using `joblib.Parallel` with `dask` as a back-end

See the following issue: [`joblib/issues/875`](https://github.com/joblib/joblib/issues/875) for explanation.

## Setup

Clone this repo 
```bash
git clone git@github.com:jjerphan/mbr_lock.git
cd mbr_lock
```

To better have an understanding of what's going on, logs have been added on branches based respectively on:
 - `1.28.0` for `distributed`
 - `0.13.2` for `joblib`

You can have access to them cloning the following repositories and installing them as dependencies

### Getting forks
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

I recommand directly pulling dependencies and installing with the forks:
```bash
pip install pandas==0.24.2
pip install scikit-learn==0.21.1
pip install -e ./joblib
pip install -e ./distributed
```

### Reproduce deadlock

Execute and output stderr and stdout in a logfile

```bash
python main.py 2>&1 | tee logs
# then ^C when hanging
```

### Analyse logs

Use scripts present in `tools`.

```bash
tools/lock_logs logs
tools/count_logs logs 
```


