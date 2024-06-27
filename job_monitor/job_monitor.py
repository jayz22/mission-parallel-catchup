import os
import redis
import requests
import json
import sys
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, UTC

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
JOB_QUEUE = os.getenv('JOB_QUEUE', 'ranges')
FAILED_QUEUE = os.getenv('FAILED_QUEUE', 'failed')
WORKER_PREFIX = os.getenv('WORKER_PREFIX', 'stellar-core')
NAMESPACE = os.getenv('NAMESPACE', 'default')
WORKER_COUNT = int(os.getenv('WORKER_COUNT', 3))
LOGGING_INTERVAL_SECONDS = int(os.getenv('LOGGING_INTERVAL_SECONDS', 10))

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Configure logging
log_file_name = f"job_monitor_{datetime.now(UTC).strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_file_path = os.path.join('/data', log_file_name)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(sys.stdout),
    logging.FileHandler(log_file_path),
])
logger = logging.getLogger()

# In-memory status data structure and threading lock
status = {
    'jobs_remain': 0,
    'jobs_failed': 0,
    'workers': []
}
status_lock = threading.Lock()

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with status_lock:
                self.wfile.write(json.dumps(status).encode())                
        else:
            self.send_response(404)
            self.end_headers()

def update_status():
    global status
    while True:
        try:
            # Check the queue status
            jobs_remain = redis_client.llen(JOB_QUEUE)
            jobs_failed = redis_client.llen(FAILED_QUEUE)

            # Ping each worker status
            worker_statuses = []
            for i in range(WORKER_COUNT):
                worker_name = f"{WORKER_PREFIX}-{i}.{WORKER_PREFIX}.{NAMESPACE}.svc.cluster.local"
                try:
                    response = requests.get(f"http://{worker_name}:11626/info")
                    logger.debug("Worker %s is running, response: %d", worker_name, response.status_code)
                    worker_statuses.append({'worker_id': i, 'status': 'running', 'response': response.status_code})
                except requests.exceptions.RequestException:
                    logger.debug("Worker %s is down", worker_name)
                    worker_statuses.append({'worker_id': i, 'status': 'down'})

            # update the status
            with status_lock:
                status = {
                    'jobs_remain': jobs_remain,
                    'jobs_failed': jobs_failed,
                    'workers': worker_statuses
                }                
            logger.info("Status: %s", json.dumps(status))
        except Exception as e:
            logger.error("Error while getting status: %s", str(e))

        time.sleep(LOGGING_INTERVAL_SECONDS)

def run(server_class=HTTPServer, handler_class=RequestHandler):
    server_address = ('', 8080)
    httpd = server_class(server_address, handler_class)
    logger.info('Starting httpd server...')
    httpd.serve_forever()

if __name__ == '__main__':
    log_thread = threading.Thread(target=update_status)
    log_thread.daemon = True
    log_thread.start()    

    run()
