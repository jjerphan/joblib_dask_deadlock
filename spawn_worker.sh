#!/usr/bin/env bash

#
# Run infrastructure locally using Docker
#

NB_WORKERS=10
REPOSITORY_NAME=jjerphan/joblib_dask_deadlock
TAG=dask_ml

IMAGE_NAME=$REPOSITORY_NAME:$TAG

# Stop script on errors
set -e

\echo "[+] Building image $IMAGE_NAME locally"
\docker build . -t $IMAGE_NAME

# Launching one server
\echo "[+] Running the server "

server_id=$(docker run -d --name=joblib_dask_deadlock_server $IMAGE_NAME server)
ip_address_server=$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' $server_id)

# Launching workers
for i in $(seq $NB_WORKERS)
do
    docker run $IMAGE_NAME \
        --name joblib_dask_deadlock_worker_$1 \
        - e DASK_SCHEDULER_ADDRESS=$ip_address_server \
        - e DASK_SCHEDULER_PORT=8786 \
        worker
done