import logging

from joblib import parallel_backend
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from distributed import Client

"""
A simple reproducible example of a dead-lock on `joblib.Parallel`
and `dask` as a back-end.
"""

if __name__ == "__main__":
    logging.debug("Started reproducible example")
    X, y = make_classification(n_samples=4898, n_features=120,
                               n_informative=2, n_redundant=2,
                               n_repeated=0, n_classes=2,
                               n_clusters_per_class=2,
                               random_state=42)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

    estimator = RandomForestClassifier()

    param_grid = {
        'bootstrap': [True, False],
        'max_depth': [10, 30, 50, 70, 90, None],
        'min_samples_leaf': [1, 2, 4],
        'min_samples_split': [2, 5, 10],
        'n_estimators': [200, 600, 1000, 1400, 1800]
    }

    gs_estimator = GridSearchCV(estimator, param_grid)

    logging.debug("Creating Dask Client")
    dask_client = Client()
    logging.debug("Created Dask Client")

    logging.debug("Entering Dask Context")
    with parallel_backend("dask"):
        logging.debug("Entered Dask Context")

        logging.debug("Launching Grid-Search")
        gs_estimator.fit(X_train, y_train)

        # --> The following code is not executed

        logging.debug("Done with Grid-Search")
        logging.debug("Exiting Dask context")

    logging.debug("Exited Dask context")

    logging.debug("Done")

