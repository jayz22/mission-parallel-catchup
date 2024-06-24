#!/bin/bash

REDIS_HOST="redis-cluster"
REDIS_PORT=6379
SLEEP_INTERVAL=5
WORKER_ID=$(hostname | awk -F'-' '{print $NF}')
BACKUP_QUEUE="backup_${WORKER_ID}"
FAILED_QUEUE="failed_queue"
JOB_QUEUE="job_queue"

# Function to fetch jobs from the backup queue
fetch_backup_jobs() {
  while true; do
    JOB_KEY=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT LPOP $BACKUP_QUEUE)
    if [ -n "$JOB_KEY" ]; then
      echo "Processing backup job: $JOB_KEY"
      process_job $JOB_KEY
    else
      echo "No more jobs in the backup queue."
      break
    fi
  done
}

# Function to process a job
process_job() {
  local job_key=$1
  ./stellar-core catchup $job_key
  if [ $? -ne 0 ]; then
    echo "Error processing job: $job_key"
    redis-cli -h $REDIS_HOST -p $REDIS_PORT RPUSH $FAILED_QUEUE $job_key
  else
    echo "Successfully processed job: $job_key"
  fi
}

# Main loop
while true; do
  # First, process any jobs from the backup queue
  fetch_backup_jobs

  # Fetch jobs from the actual queue using BRPOPLPUSH
  JOB_KEY=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT BRPOPLPUSH $JOB_QUEUE $BACKUP_QUEUE 0)
  if [ -n "$JOB_KEY" ]; then
    echo "Processing job: $JOB_KEY"
    process_job $JOB_KEY
  else
    echo "No more jobs in the queue. Sleeping for $SLEEP_INTERVAL seconds..."
    sleep $SLEEP_INTERVAL
  fi
done
