# WIP : Trying to reproduce error with Dask ML

### Setup

To better have an understanding of what's going on, logs have been added on branches based respectively on:
 - [`jjerphan/distributed 1.28.0`](https://github.com/jjerphan/distributed/pull/2) for logs on `1.28.0` for `distributed`
 - [`jjerphan/joblib 0.13.2`](https://github.com/jjerphan/joblib/pull/1) for logs on `0.13.2` for `joblib`

Install dependencies including those two modifications of `distributed` and `joblib` with:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run

The the code of `example.py` in a python interpreter. Logs will appear.

See [`logs.txt`](./logs.txt) for an example of such logs.


### Inspect logs

You can use scripts in the `scripts` to have a better understanding of logs
```bash
# To count occurrences of logs
scripts/count_logs logs.txt

# To display logs related to the lock in Parallel
scripts/lock_logs logs.txt

# To display occurrences of logs related to the lock in Parallel
cat logs.txt | scripts/lock_logs | scripts/count_logs | sort
```
