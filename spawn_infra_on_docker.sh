#!/usr/bin/env bash

#
# Run infrastructure locally using Docker
#

NB_WORKERS=10
REPOSITORY_NAME=jjerphan/joblib_dask_deadlock
TAG=dask_ml

IMAGE_NAME=${REPOSITORY_NAME}:${TAG}

# Stop script on errors
set -e

\echo "[+] Building image $IMAGE_NAME locally"
\docker build . -t ${IMAGE_NAME}

# Launching one server
\echo "[+] Running the server "

run_command="docker run --name=joblib_dask_deadlock_server -p 8787:8787 -d $IMAGE_NAME server"
\echo ${run_command}

server_id=$(eval ${run_command})

inspect_command='docker inspect --format "{{ .NetworkSettings.IPAddress }}" $server_id'
\echo ${inspect_command}

ip_address_server=$(eval ${inspect_command})

\echo "[+] Server on container $server_id with IP $ip_address_server"


# Launch workers in parallel
(seq ${NB_WORKERS}) | xargs -P $NB_WORKERS -I % bash -c "docker run --name=joblib_dask_deadlock_worker_% -d -e DASK_SCHEDULER_ADDRESS=$ip_address_server -e DASK_SCHEDULER_PORT=8786 $IMAGE_NAME worker"