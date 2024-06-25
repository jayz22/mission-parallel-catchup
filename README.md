## Summary

This is the prototype for the new parallel catchup mission (revamps the current mission 'HistoryPubnetParallelCatchup').

## Repo structure
The mission is logically divided into two parts: 1. parallel-catchup, which consists of components of the core catchup logic, that live inside Kubernetes. 2. the mission, which is the client that interacts with the Kubernetes. 

[parallel-catchup](https://github.com/jayz22/mission-parallel-catchup/tree/master/parallel-catchup) contains the Helm chart of the Kubernetes project. 
[mission](https://github.com/jayz22/mission-parallel-catchup/tree/master/mission) contains the mission. 

## How to Run
`$ cd ./mission`

`$ python3 -m venv venv`

`$ source venv/bin/activate`

`$ pip install -f requirements.txt`

`$ python parallel_catchup.py`

Then use kubectl to monitor the status and logs of the pods. 
