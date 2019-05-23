"""
    Minimal reproducible example.
    To be run in an interpreter.
"""
from sklearn.datasets import make_classification
from sklearn.tree import DecisionTreeRegressor

from dask_ml.model_selection import GridSearchCV as DaskGridSearchCV
from distributed import Client
from distributed import LocalCluster
from joblib import parallel_backend

X, y = make_classification(n_samples=16870,
                           n_features=762,
                           n_classes=5,
                           n_informative=760,
                           random_state=42)

estimator = DecisionTreeRegressor()

param_grid = {
    'max_depth': [10],
    'min_samples_leaf': [1, 2],
    'min_samples_split': [2],
}

gs_estimator = DaskGridSearchCV(estimator=estimator,
                                param_grid=param_grid)

cluster = LocalCluster()
client = Client(cluster)

with parallel_backend("dask"):
    gs_estimator.fit(X, y)

print(gs_estimator)
