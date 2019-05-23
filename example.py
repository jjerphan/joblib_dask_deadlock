"""
    Minimal reproducible example.

        see: https://github.com/dask/distributed/issues/2149

    To be run in an interpreter.
"""
import numpy as np

from dask.distributed import Client, LocalCluster
from joblib import Parallel, delayed, parallel_backend


def sum_values(array, scalar):
    return (array + scalar).sum()


cluster = LocalCluster()
client = Client(cluster)

with parallel_backend("dask"):
    results = Parallel()(delayed(sum_values)(np.zeros(i), 5) for i in range(50000, 50010))

print(results)
