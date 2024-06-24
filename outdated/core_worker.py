import redis
import subprocess
import time

# Initialize Redis connection
job_queue = redis.Redis(host='redis', port=6379)

while True:
    job = job.queue.rpop('ranges')
    if job:
        range = job.decode('utf-8')
        result = subprocess.run(["/usr/bin/stellar-core", "--conf", "/config/stellar-core.cfg", "new-db"], capture_output=True, text=True)
        result = subprocess.run(["/usr/bin/stellar-core", "--conf", "/config/stellar-core.cfg", "catchup", range, "--metric", "ledger.transaction.apply"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
        else:
            print(f"Job {range} completed successfully")
    else:
        print("No more jobs in the queue. Sleeping for a bit...")
        time.sleep(5)
