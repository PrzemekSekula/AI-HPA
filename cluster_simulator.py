import numpy as np

from time import time
from random import random

class Task:
    """
    A simple class that represents a task (request)
    This request should be send to pods by deployments
    Parameters:
        life_time  - life time of the task (microseconds)
        start_time - creation time of a task
    Methods:
        isAlive()     - checks if task still exists (lives no longer than life_time)
        getLifeTime() - returns the life time of the task
    """
    
    def __init__(self, life_time = 10000):

        self.life_time = life_time
        self.start_time = time()
        
    def isAlive(self):
        return self.getLifeTime() < self.life_time
    
    def getLifeTime(self):
        """
        Returns life time of the task (in microseconds)
        """
        return 1e6 * (time() - self.start_time)

    
    
class Metric:
    """
    A simple class that facititates accessing a single deployment metrics.
    
    Parameters correspond to collected metrics:
        pods       - Total number of pods        
        activePods - number of active pods (pods involved in tasks)
        cpu        - total cpu usage
        memory     - total memory usage
        queueTasks - number of not started tasks
        tasksDone  - number of done tasks (counter)
        nrDead     - number of dead (expoired) tasks. This is not
                     returned by Deployment.getMetrics, so it should
                     be added to the list or will be set to None
    
    Methods:
        setMetric() - sets the metric based on the list returned
                      by Deployment.getMetrics(). It is possible to 
                      set metric also in constructor.
    """
    
    def __init__(self, metric):
        if metric is None:
            self.pods = None
            self.activePods = None
            self.cpu = None
            self.memory = None
            self.queueTasks = None
            self.nrDone = None
            self.nrDead = None
        else:
            self.setMetric(metric)
            
    def setMetric(self, metric):
        """
        Sets the metric based on the list returned by Deployment.getMetrics()
        The order of the input list metrics must follow the order of the 
        class parameters, described in the class documentation.
        """
        if len(metric) < 7:
            metric = metric + [None] * (7 - len(metric))
            
        self.pods = metric[0]
        self.activePods = metric[1]
        self.cpu = metric[2]
        self.memory = metric[3]
        self.queueTasks = metric[4]
        self.nrDone = metric[5]
        self.nrDead = metric[6]
            
    
    
class Pod:
    """
    A class that represents a Pod.
    Parameters:
        duration_task - how many cycles per task (on average, microseconds)
        duration_rand - duration randomness (0.1 = +-10%)
        cpu_task      - cpu occupation per task (on average)
        cpu_rand      - cpu randomness (0.1 = +-10%)
        cpu_base      - cpu occupation for an empty pod
        memory_task   - cpu occupation per task (on average)
        memory_rand   - cpu randomness (0.1 = +-10%)
        memory_base   - memory occupation for an empty pod
        task   - processed task (None if the pod is free)
        cpu    - current CPU usage
        memory - current memory usage
        
        
    Methods:
        isBusy()        - checks if pod is busy
        startTask(task) - starts a task
        checkDone()     - checks if task is done
    """

    
    
    def __init__(
        self,
        duration_task = 1000, duration_rand = 0.1,
        cpu_task = 20, cpu_rand = 0.1, cpu_base = 1,
        memory_task = 20, memory_rand = 0.1, memory_base = 1
    ):
        
        self.duration_task = duration_task
        self.duration_rand = duration_rand
        self.cpu_task = cpu_task
        self.cpu_rand = cpu_rand
        self.cpu_base = cpu_base
        self.memory_task = memory_task
        self.memory_rand = memory_rand
        self.memory_base = memory_base
        
        self.resetStats()
    
    def resetStats(self):
        self.task = None
        self.start_time = None
        self.end_time = None
        
        self.cpu = self.cpu_base
        self.memory = self.memory_base
        
        
    def isBusy(self):
        return self.task is not None
        
    def startTask(self, task):
        """
        Starts a task
        Arguments:
            task - an instance of a Task class
        Returns: 
            0  - task started
            -1 - pod is already busy
        """
        if self.isBusy():
            return -1
        self.task = task
        self.start_time = time()
        self.end_time = self.start_time + self.duration_task * ( 1 + (random() - random()) * self.duration_rand) / 1e6
        self.end_time = max(self.end_time, self.start_time)
        
        self.cpu = self.cpu_base + self.cpu_task * (1 + (random() - random()) * self.cpu_rand)
        self.memory = self.memory_base + self.memory_task * (1 + (random() - random()) * self.memory_rand)
        
        return 0
    
    def checkDone(self):
        """
        Returns:
            -1   - pod was not busy
            0    - not done (pod is working)
            task - an object of a task that the pod had just finished
        """
        if not self.isBusy():
            return -1
        elif time() < self.end_time:
            return 0
        else:
            task = self.task
            self.resetStats()
            return task

        
class Deployment:
    """
    A class that represents a Deployment.
    Gneral parameters:
        pods         - list of pods
        to_remove    - number of pods to remove
        tasks        - list of tasks to be performed
        tasks_done   - list of tasks that already were performed
        nr_done      - counter that counts done tasks
        
    Parameters used to set up pods:
        duration_task - how many cycles per task (on average, microseconds)
        duration_rand - duration randomness (0.1 = +-10%)
        cpu_task      - cpu occupation per task (on average)
        cpu_rand      - cpu randomness (0.1 = +-10%)
        cpu_base      - cpu occupation for an empty pod
        memory_task   - cpu occupation per task (on average)
        memory_rand   - cpu randomness (0.1 = +-10%)
        memory_base   - memory occupation for an empty pod
        
    Methods:
        addPod()        - adds a pod
        removePod()     - removes a pod
        update()        - updates a state of the deployment
        getMetrics()    - returns deployment's metrics
    """    
    
    def __init__(
        self,
        starting_pods = 1,
        duration_task = 1000, duration_rand = 0.1,
        cpu_task = 20, cpu_rand = 0.1, cpu_base = 1,
        memory_task = 20, memory_rand = 0.1, memory_base = 1
    ):
        """
        Arguments:
        starting_pods = how many pods should be run when the deployment is created
        """

        self.to_remove = 0
        self.nr_done = 0
        
        self.tasks = []
        self.tasks_done = []        
        self.pods = []
        
        
        self.duration_task = duration_task
        self.duration_rand = duration_rand
        self.cpu_task = cpu_task
        self.cpu_rand = cpu_rand
        self.cpu_base = cpu_base
        self.memory_task = memory_task
        self.memory_rand = memory_rand
        self.memory_base = memory_base
        
        for i in range(starting_pods):
            self.addPod()
        
        
    def addPod(self):
        """
        Adds a new pod
        """
        self.pods.append(Pod(
            self.duration_task, self.duration_rand,
            self.cpu_task, self.cpu_rand, self.cpu_base,
            self.memory_task, self.memory_rand, self.memory_base
        ))
                    
    def removePod(self):
        """
        Removes a pod from the deployment. If all the pods are busy, the
        deployment waits until one pod is free. The number of pods
        cannot be less than 1.
        """
        self.to_remove += 1
        self.update()
        
    def update(self):
        # First let's check the tasks
        to_remove_list = []
        for i, pod in enumerate(self.pods):
            done = pod.checkDone()
            if done == -1:
                if self.to_remove > 0:
                    to_remove_list.append(i)
                    self.to_remove -= 1
            elif done != 0:
                self.nr_done += 1
                self.tasks_done.append(done)
                
        ### Remove unwanted pods
        for r in to_remove_list:
            if len(self.pods) > 1:
                self.pods.pop(r)
        
        # now we can start new tasks
        for pod in self.pods:
            if len(self.tasks) > 0:
                if not pod.isBusy():
                    task = self.tasks.pop(0)
                    pod.startTask(task)
            
    def addTask(self, task):
        """
        Adds a task to the deployment. This task is sentto one of the 
        vacant pods, or (if all pods are busy) waits in the queue.
        """
        self.tasks.append(task)
        self.update()
            
    def getMetrics(self):
        """
        Returns:
            nr_pods, active_pods, cpu, memory, nr_tasks, nr_done
            - Total number of pods
            - number of active pods (pods involved in tasks)
            - total cpu usage
            - total memory usage
            - number of not started tasks
            - number of done tasks (counter)
        """
        self.update()
        cpu = 0
        memory = 0
        nr_pods = len(self.pods)
        active_pods = 0
        for pod in self.pods:
            if pod.isBusy():
                active_pods += 1
            cpu += pod.cpu
            memory += pod.memory
        return [nr_pods, active_pods, np.round(cpu, 2), np.round(memory, 2), len(self.tasks), self.nr_done]
            
    def getTasksDone(self):
        """
        Returns all done tasks. The returned tasks are not longer stored in the
        Deployment.
        Returns:
            List of tasks that are already finished.
        """
        tasks = self.tasks_done
        self.tasks_done = []
        return tasks
    
    
class SimpleCluster:
    """
    A class that represents a simple cluster.
    You can define the number of deployments, and the incoming tasks are going 
    through the deployments in series (from first to last deployment).
    
    Parameters:
        deployments - list of deployments (instances of class Deployment)
        tasks       - list of tasks (instances of class Task)
       
        
    Methods:
        addTasks()          - adds tasks to the queue
        update()            - updates the state od the cluster. Usually called
                              by getMetrics(), no need to run it manually
        getMetrics()        - updates the states of the cluster and returns 
                              the metrics
        updateDeployments() - Updates deployments (adds/removes pods)
    """
    
    def __init__(self, durations = [1e3, 1e3, 1e3], pods = None):
        """
        Arguments:
            durations - average task duration for each Deployment. 
            pods      - number of starting pods for each deployment
        """
        if pods is None:
            pods = [1] * len(durations)
            
        self.deployments = []
        for duration, pod in zip(durations, pods):
            self.deployments.append(Deployment(
                starting_pods = pod,
                duration_task = duration))
        
        self.tasks = []
        
        self.tasks_dead = []
        self.tasks_done = []
        self.total_dead = 0
        
        
    def addTasks(self, nr_tasks, life_time = 1e6):
        """
        Adds new tasks to the cluster. The tasks are assigned to the 
        consecutive deployments.
        Arguments:
            nr_tasks  - number of tasks to add
            life_time - life time of tasks
        """
        for i in range(nr_tasks):
            self.tasks.append(Task(life_time = life_time))
            
        self.update()
        
    def update(self):
        tasks = self.tasks
            
        nr_dead_list = [0] * len(self.deployments)
        for dep_nr, deployment in enumerate(self.deployments):                    
            for task in tasks:
                deployment.addTask(task)
                if task in self.tasks:
                    self.tasks.remove(task)
                
            base_tasks = deployment.getTasksDone()
            tasks = []
            for task in base_tasks:
                if task.isAlive():
                    tasks.append(task)
                else:
                    nr_dead_list[dep_nr] += 1
        
            lifetimes = [task.getLifeTime() for task in tasks]
        
        return lifetimes, nr_dead_list
    
    def getMetrics(self):
        lifetimes, nr_dead_list = self.update()
        self.total_dead += np.sum(nr_dead_list)
        res = [self.total_dead, [np.round(lifetime) for lifetime in lifetimes]]
        for nr_dead, deployment in zip(nr_dead_list, self.deployments):
            res.append(deployment.getMetrics() + [nr_dead])
        return res
    
    def updateDeployments(self, actions):
        """
        Updates deployments by changing the number of pods
        Arguments:
            actions - list of actions. Allowed actions:
                None - does not change anything
                1    - increases the number of pods by 1
                -1   - decreseas the number of pods by 1
        """
        for action, deployment in zip(actions, self.deployments):
            if action == 1:
                deployment.addPod()
            elif action == -1:
                deployment.removePod()
        