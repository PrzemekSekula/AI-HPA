# AI HPA - Cluster simulator

This is a first attempt to prepare and test a simple cluster simulator. The goals of this repo are as follows:
- long term goal: Create AI HPA simulator
- mid term goal: Test different RL algorithms on a simple  cluster simulator and be prepared to run these algorithms on a real cluster
- short term goal: build a simple cluster simulator and apply any algorithm to scale pods.

## Getting started
No extra actions required, assuming that you installed Anaconda, you can just download and run the repo.

## File structure
- `cluster_simulator.py` - simulator of a cluster. A library with a bunch of classes.
- `ClusterTests.ipynb` - a notebook that tests the simulator and simple scalling heuristics.
- `REDME.md` - this file

## Cluster simulator description
This section contains a description of `cluster_simulator.py` library. This library contains 4 classes.

#### Task
A class that represents a task. Currently the only thing that tasks can do is to expire, so every task has `life_time` and `start_time` variables that can control it. To check the life time of the task you should use `isAlive()` or `getLifeTime()` methods.

#### Metric
A simple class that facititates accessing a single deployment metrics.

#### Pod 
A basic structure of the simulator that represents a pod. Tasks should be send to pods, processed with pods and then returned. The pod also emulates CPU and memory usage. The durations of tasks, as well as CPU and memory usages are controlled by pods.

#### Deployment
The main class in this repo. The role of the deployment is to control pods and tasks. Each deployment contains one or more pods. Each deployment can receive tasks. When a deployment receives a tasks it sends it to the pod or (if all pods are busy), keeps it in the queue. The finised tasks are kept in the deployment and may be returned with `getTasksDone()` method.

#### SimpleCluster
A class that represents a simple cluster. You can define the number of deployments, and the incoming tasks are going through the deployments in series (from first to last deployment). This class serves mainly for test purposes

*Note: The basic time unit for this library is a microsecond.*
