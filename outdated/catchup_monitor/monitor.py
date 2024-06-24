import redis
import requests
import time
from flask import Flask
from flask_socketio import SocketIO, emit

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Redis connection
r = redis.Redis(host='redis', port=6379)

# List of stellar-core instances (assumes these are known ahead of time)
stellar_core_instances = [
    'http://stellar-core-0:11625',
    'http://stellar-core-1:11625',
    'http://stellar-core-2:11625'
]

def check_queue():
    return r.llen('job_queue')

def ping_stellar_core():
    statuses = []
    for instance in stellar_core_instances:
        try:
            response = requests.get(instance)
            statuses.append(response.status_code == 200)
        except requests.ConnectionError:
            statuses.append(False)
    return statuses

def job_monitor():
    while True:
        queue_size = check_queue()
        stellar_statuses = ping_stellar_core()
        all_stellar_down = all(not status for status in stellar_statuses)
        
        if queue_size == 0 and all_stellar_down:
            job_status = "done"
        else:
            job_status = "running"
        
        socketio.emit('job_status', {'status': job_status})
        time.sleep(5)

@app.route('/')
def index():
    return "Job Monitor Service"

if __name__ == "__main__":
    from threading import Thread

    # Start the job monitor in a separate thread
    monitor_thread = Thread(target=job_monitor)
    monitor_thread.start()

    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000)
