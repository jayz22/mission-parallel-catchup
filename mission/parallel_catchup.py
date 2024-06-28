import subprocess
import yaml
import tempfile
import os
import time
import requests
import logging
import sys
import atexit
import signal

# Constants
HELM_RELEASE_NAME = "parallel-catchup"
HELM_CHART_PATH = "../parallel-catchup"
VALUES_FILE_PATH = "../parallel-catchup/values.yaml"

# config
worker_replicas = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger()

# function to cleanup the project on exit
def on_exit():
    run_command(["helm", "uninstall", HELM_RELEASE_NAME])

atexit.register(on_exit)

def signal_handler(signum, frame):
    print(f"Received signal {signum}, exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl-C
signal.signal(signal.SIGTERM, signal_handler) # Handle termination signal

def run_command(command):
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logger.info(f"Command '{command}' failed with error: {e.stderr.decode('utf-8')}")
        return None

def install_project():    
    logger.info("Installing Helm chart...")

    with open(VALUES_FILE_PATH, 'r') as file:
        values = yaml.safe_load(file)
    values['worker']['replicas'] = worker_replicas

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    with open(temp_file.name, 'w') as file:
        yaml.dump(values, file)

    run_command(["helm", "install", HELM_RELEASE_NAME, HELM_CHART_PATH, "--values", temp_file.name])
    os.remove(temp_file.name)

def get_job_monitor_status():
    try:
        response = requests.get(f"http://ssc-job-monitor.services.stellar-ops.com/status")
        print(response.json())
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error querying job monitor: {e}")
        return None

def main():
    install_project()

    while True:
        status = get_job_monitor_status()
        if status:
            queue_size = status.get('jobs_remain', 1)  # Default to 1 to keep running if not available
            all_workers_down = all(worker['status'] == 'down' for worker in status.get('workers', []))

            if queue_size == 0 and all_workers_down:
                print("Queue is empty and all workers are down. Cleaning up resources...")
                break

        time.sleep(10)

if __name__ == '__main__':
    main()
