import os
import redis
import requests
import json
import sys
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
JOB_QUEUE = os.getenv('JOB_QUEUE', 'ranges')
FAILED_QUEUE = os.getenv('FAILED_QUEUE', 'failed')
WORKER_PREFIX = os.getenv('WORKER_PREFIX', 'stellar-core')
NAMESPACE = os.getenv('NAMESPACE', 'default')
WORKER_COUNT = int(os.getenv('WORKER_COUNT', 3))

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger()

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = self.get_status()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def get_status(self):
        # Check the queue size
        jobs_remain = redis_client.llen(JOB_QUEUE)
        jobs_failed = redis_client.llen(FAILED_QUEUE)

        # Ping each worker
        worker_statuses = []
        for i in range(WORKER_COUNT):
            worker_name = f"{WORKER_PREFIX}-{i}.{WORKER_PREFIX}.{NAMESPACE}.svc.cluster.local"
            try:
                response = requests.get(f"http://{worker_name}:11626/info")
                logger.info("Worker %s is running, response: %d", worker_name, response.status_code)
                worker_statuses.append({'worker': worker_name, 'status': 'running', 'response': response.status_code})
            except requests.exceptions.RequestException:
                logger.error("Worker %s is down", worker_name)
                worker_statuses.append({'worker': worker_name, 'status': 'down'})

        return {'jobs_remain': jobs_remain, 'jobs_failed': jobs_failed, 'workers': worker_statuses}

def log_status():
    while True:
        try:
            handler = RequestHandler
            status = handler.get_status(handler)
            logger.info("Status: %s", json.dumps(status))
        except Exception as e:
            logger.error("Error while getting status: %s", str(e))
        time.sleep(5)

def run(server_class=HTTPServer, handler_class=RequestHandler):
    server_address = ('', 8080)
    httpd = server_class(server_address, handler_class)
    logger.info('Starting httpd server...')
    httpd.serve_forever()

if __name__ == '__main__':
    # Start the periodic logging in a separate thread
    # for testing only, will disable this in production
    log_thread = threading.Thread(target=log_status)
    log_thread.daemon = True
    log_thread.start()    

    run()
