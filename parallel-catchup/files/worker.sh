SLEEP_INTERVAL=10
LOG_DIR="/data"
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
JOB_QUEUE=$JOB_QUEUE
SUCCESS_QUEUE=$SUCCESS_QUEUE
FAILED_QUEUE=$FAILED_QUEUE
PROGRESS_QUEUE=$PROGRESS_QUEUE

while true; do
# Fetch the next job key from the Redis queue. 
# The queue operation is always push left pop right. 
JOB_KEY=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT LMOVE $JOB_QUEUE $PROGRESS_QUEUE RIGHT LEFT)

if [ -n "$JOB_KEY" ]; then
    echo "Processing job: $JOB_KEY"
    /usr/bin/stellar-core --conf /config/stellar-core.cfg new-db
    /usr/bin/stellar-core --conf /config/stellar-core.cfg catchup $JOB_KEY --metric 'ledger.transaction.apply'
    if [ $? -ne 0 ]; then
    echo "Error processing job: $JOB_KEY"
    redis-cli -h $REDIS_HOST -p $REDIS_PORT LPUSH $FAILED_QUEUE $JOB_KEY
    else
    echo "Successfully processed job: $JOB_KEY"
    redis-cli -h $REDIS_HOST -p $REDIS_PORT LPUSH $SUCCESS_QUEUE $JOB_KEY
    redis-cli -h $REDIS_HOST -p $REDIS_PORT LREM $PROGRESS_QUEUE -1 $JOB_KEY
    fi

    # Parse and extract the metrics from the log file
    LOG_FILE=$(ls -t $LOG_DIR/stellar-core-*.log | head -n 1)
    if [ -z "$LOG_FILE" ]; then
    echo "No log file found."
    exit 1
    fi

    transaction_sum=$(tac "$LOG_FILE" | grep -m 1 -B 11 "metric 'ledger.transaction.apply':" | grep "sum =" | awk '{print $NF}')
    echo "Log file: $LOG_FILE"
    echo "ledger.transaction.apply sum: $transaction_sum"

else
    echo "No more jobs in the queue. Sleeping for $SLEEP_INTERVAL seconds..."
    sleep $SLEEP_INTERVAL
fi
done