#!/bin/bash
source activate /opt/conda/envs/clustervw_env_t
flask db upgrade
flask translate compile

(cd redis-stable && ./src/redis-server redis.conf) &
rq worker clusterv-tasks --path `pwd` &
rq worker clusterv-tasks --path `pwd` &
rq worker clusterv-tasks --path `pwd` &
rq worker clusterv-tasks --path `pwd` & 
exec gunicorn -b :5000 --access-logfile - --error-logfile - run_clusterv_web:app
#flask run --host=0.0.0.0

#(cd redis-stable && ./src/redis-server redis.conf)

