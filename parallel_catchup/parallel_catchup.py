import os
import time
import requests
import yaml
from kubernetes import client, config
from kubernetes.client import V1DeleteOptions

# Load Kubernetes configuration
config.load_kube_config()

# Kubernetes API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

# Paths to your YAML files
REDIS_QUEUE_YAML = 'redis_queue.yaml'
JOB_MONITOR_YAML = 'job_monitor.yaml'
CATCHUP_WORKER_YAML = 'catchup_worker.yaml'

# Job monitor status endpoint
JOB_MONITOR_URL = 'http://<job-monitor-url>/status'  # Replace with actual URL

# Utility function to create resources from YAML files
def create_resource_from_yaml(yaml_file, replicas=None):
    with open(yaml_file) as f:
        documents = list(yaml.safe_load_all(f))
        for document in documents:
            if replicas is not None and 'kind' in document and document['kind'] in ['Deployment', 'StatefulSet']:
                # Set the number of replicas if specified
                document['spec']['replicas'] = replicas
            if 'kind' in document:
                kind = document['kind']
                if kind == 'Service':
                    v1.create_namespaced_service(namespace='default', body=document)
                elif kind == 'Deployment':
                    apps_v1.create_namespaced_deployment(namespace='default', body=document)
                elif kind == 'StatefulSet':
                    apps_v1.create_namespaced_stateful_set(namespace='default', body=document)
                elif kind == 'ConfigMap':
                    v1.create_namespaced_config_map(namespace='default', body=document)
                # Add other kinds as necessary

# Create the resources with specified replicas
create_resource_from_yaml(REDIS_QUEUE_YAML)
create_resource_from_yaml(JOB_MONITOR_YAML)
create_resource_from_yaml(CATCHUP_WORKER_YAML, replicas=5)  # Set the number of worker replicas here

# Function to get job monitor status
def get_job_monitor_status():
    try:
        response = requests.get(JOB_MONITOR_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error querying job monitor: {e}")
        return None

# Function to delete all resources
def delete_all_resources():
    # Delete deployments
    apps_v1.delete_namespaced_deployment(name='job-monitor', namespace='default', body=V1DeleteOptions())
    apps_v1.delete_namespaced_deployment(name='redis-queue', namespace='default', body=V1DeleteOptions())
    # Delete stateful sets
    apps_v1.delete_namespaced_stateful_set(name='catchup-worker', namespace='default', body=V1DeleteOptions())
    # Delete services
    v1.delete_namespaced_service(name='job-monitor', namespace='default')
    v1.delete_namespaced_service(name='redis-queue', namespace='default')

# Main loop to monitor and clean up resources
while True:
    status = get_job_monitor_status()
    if status:
        queue_size = status.get('queue_size', 1)  # Default to 1 to keep running if not available
        all_workers_down = all(worker['status'] == 'down' for worker in status.get('workers', []))

        if queue_size == 0 and all_workers_down:
            print("Queue is empty and all workers are down. Cleaning up resources...")
            delete_all_resources()
            break

    time.sleep(10)  # Sleep for 10 seconds before next check
