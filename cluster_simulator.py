import numpy as np
import simpy 

from time import time
from random import random

class Metric:
    """
    A simple class that facititates accessing a single deployment metrics.
    
    Parameters correspond to collected metrics:
        pods        - Total number of pods        
        activePods  - number of active pods (pods involved in tasks)
        activeTasks - number of active (processed) tasks 
        cpu         - total cpu usage
        cpu_max     - maximum cpu capacity
        memory      - total memory usage
        memory_max  - maximum memory capacity
        queueTasks  - number of not started tasks
        nrDone      - number of done tasks (counter)
        nrDead      - number of dead (expired) tasks (counter).
        nrErr5xx    - number of 5xx errors (tasks not accepted by the)
                      deployment (counter)
    
    Methods:
        setMetric()  - sets the metric based on the list returned
                       by Deployment.getMetrics(). It is possible to 
                       set metric also in constructor.
        metric2dic() - returns a dictionary with metric data 
    """
    
    def __init__(self, metric):
        if metric is None:
            self.pods = None
            self.activePods = None
            self.activeTasks = 0
            self.cpu = None
            self.cpu_max = None
            self.memory = None
            self.memory_max = None
            self.queueTasks = None
            self.nrDone = None
            self.nrDead = None
            self.nrErr5xx = None
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
        self.activeTasks = metric[2]
        self.cpu = metric[3]
        self.cpu_max = metric[4]
        self.memory = metric[5]
        self.memory_max = metric[6]
        self.queueTasks = metric[7]
        self.nrDone = metric[8]
        self.nrDead = metric[9]
        self.nrErr5xx = metric[10]
        
    def metric2dic(self):
        """
        Returns a dictionary with metric data
        """
        return {
            'pods' : self.pods,
            'activePods' : self.activePods,
            'activeTasks' : self.activeTasks,
            'cpu' : self.cpu,
            'cpu_max' : self.cpu_max,
            'memory' : self.memory,
            'memory_max' : self.memory_max,
            'queueTasks' : self.queueTasks,
            'nrDone' : self.nrDone,
            'nrDead' : self.nrDead,
            'nrErr5xx' : self.nrErr5xx
        }



class Task:
    """
    A simple class that represents a task (request)
    This request should be send to pods by deployments
    Parameters:
        life_time      - remaining life time of the task (miliseconds)
        life_time_base - original life time of the task (miliseconds). Does not decay
        pod            - pod that is processing (or processed) the task (for logging and tests)
        deployment     - name of the last deployment (for logging and tests)
        cpu            - cpu used by pod that is processing (or processed) the task (for logging and tests)
        memory         - memory used by pod that is processing (or processed) the task (for logging and tests)
        
    Methods:
        isAlive()     - checks if task still exists (lives no longer than life_time)
        getLifeTime() - returns the life time of the task
    """
    
    def __init__(self, life_time = 10000):

        self.life_time = life_time
        self.life_time_base = life_time
        self.pod = None
        self.deployment = None
        self.cpu = None
        self.memory = None
        
    def startProcessing(self, elapsed_time, pod = None, cpu = None, memory = None):
        """ 
        Run it every time the pod is starting to process the task
        Arguments:
            elapsed_time - processing time of the task. life_time will be reduced accordingly
            pod          - processing pod
            cpu          - cpu usage by processing pod
            memory       - memory usage by processing pod
        """
        
        self.pod = pod
        self.cpu = cpu
        self.memory = memory
        
        self.updateLifeTime(elapsed_time)
                
    def updateLifeTime(self, elapsed_time):
        
        self.life_time -= elapsed_time
        
    def isAlive(self):
        """
        Checks if task is alive
        Returns:
            True / False
        """
        return self.life_time > 0

                
    
    
class Pod:
    """
    A class that represents a Pod.
    Parameters:
        env             - simpy environment 
        deployment      - deployment of the pod
        
        duration_task   - how many cycles per task (on average, miliseconds)
        duration_rand   - duration randomness (0.1 = +-10%)
        
        cpu_task        - cpu occupation per task (on average)
        cpu_rand        - cpu randomness (0.1 = +-10%)
        cpu_base        - cpu occupation for an empty pod
        cpu_max         - max available_cpu
        
        memory_task     - cpu occupation per task (on average)
        memory_rand     - cpu randomness (0.1 = +-10%)
        memory_base     - memory occupation for an empty pod
        memory_max      - max available memory
        
        nr_tasks        - total number of tasks sent to this deployment
        nr_active_tasks - number of currently processed tasks
        nt_done_tasks   - total number of done tasks
        
        
        tasks  - list of processed tasks
        cpu    - current CPU usage
        memory - current memory usage
        
        
    Methods:
        canProcess(task) - checks if the pod can process a given task
        addTask(task)    - adds a task to be performed
    """

    
    
    def __init__(
        self,
        env, 
        deployment = None,
        duration_task = 1000, duration_rand = 0.1,
        cpu_task = 20, cpu_rand = 0.1, cpu_base = 1,
        memory_task = 20, memory_rand = 0.1, memory_base = 1,
        cpu_max = 100, memory_max = 100,
    ):
        self.env = env
        self.deployment = deployment
        self.duration_task = duration_task
        self.duration_rand = duration_rand
        self.cpu_task = cpu_task
        self.cpu_rand = cpu_rand
        self.cpu_base = cpu_base
        self.memory_task = memory_task
        self.memory_rand = memory_rand
        self.memory_base = memory_base
        
        self.cpu_max = cpu_max
        self.memory_max = memory_max

        self.nr_tasks = 0
        self.nr_active_tasks = 0
        self.nr_done_tasks = 0
    
        
        self.cpu = self.cpu_base
        self.memory = self.memory_base
        
    
    def getMetricUsage(self, task, metric_task, metric_rand):
        """
        Returns a value +- random_normal(metric_rand), truncated to 3 * std
        Used internally.
        """
        std = metric_task * metric_rand
        usage = metric_task + np.random.normal(loc = 0.0, scale = std)
        usage = np.clip(
            usage, 
            usage - 3 * std,
            usage + 3 * std
        )
        return int(max(1, usage))
        
    def getCpuUsage(self, task):
        """
        Returns estimated CPU usage (includes randomness)
        """
        return self.getMetricUsage(task, self.cpu_task, self.cpu_rand)

    def getMemoryUsage(self, task):
        """
        Returns estimated memory usage (includes randomness)
        """
        return self.getMetricUsage(task, self.memory_task, self.memory_rand)
                      
    def canProcess(self, task):
        """
        Checks if the task can be processed
        Returns:
            True / False
        """        
        cpu_usage = self.getCpuUsage(task)
        if self.cpu + cpu_usage > self.cpu_max:
            return False
        
        memory_usage = self.getCpuUsage(task)
        if self.memory + memory_usage > self.memory_max:
            return False
        
        return True

    def _startTask(self, task, duration, cpu_usage, memory_usage):        
        event = simpy.events.Timeout(self.env, delay=duration)
        task.startProcessing(duration, pod = None, cpu = None, memory = None)
        yield event
        self.nr_active_tasks = max(0, self.nr_active_tasks - 1)
        #print (f'After - NOW: {self.env.now}, CPU: {self.cpu}, memory: {self.memory}, nrTasks: {self.nr_tasks}')
        self.cpu -= cpu_usage
        self.memory -= memory_usage   
        self.nr_done_tasks += 1
        if self.deployment is not None:
            self.deployment.taskDone(task)
    
    def addTask(self, task):
        """
        Adds task to the pod
        """
        self.nr_tasks += 1
        cpu_usage = self.getCpuUsage(task)
        memory_usage = self.getMemoryUsage(task)
        duration = self.getMetricUsage(task, self.duration_task, self.duration_rand)
        

        self.cpu += cpu_usage
        self.memory += memory_usage
        self.nr_active_tasks += 1

        self.env.process(self._startTask(task, duration, cpu_usage, memory_usage))
    
    

class Deployment:
    """
    A class that represents a Deployment.
    Gneral parameters:
        env          - simpy environment
        name         - name of the deployment
        cluster      - 'mother' cluster
        pods         - list of pods
        to_remove    - number of pods to remove
        tasks        - list of tasks to be performed
        queue_length - the length of the queue with new tasks
        nr_done      - counter that counts done tasks
        nr_dead      - counter that counts dead tasks
        nr_err5xx    - counter that counts 5xx errors (task not accepted)
                
    Parameters used to set up pods:
        duration_task - how many cycles per task (on average, miliseconds)
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
        taskDone(task)  - executed when the pod finishes a task
        getMetrics()    - returns deployment's metrics
    """    
    
    def __init__(
        self,
        env,
        name = None,
        cluster = None,
        starting_pods = 1,
        queue_length = 100,
        duration_task = 1000, duration_rand = 0.1,
        cpu_task = 20, cpu_rand = 0.1, cpu_base = 1,
        memory_task = 20, memory_rand = 0.1, memory_base = 1
    ):
        """
        Arguments:
        starting_pods = how many pods should be run when the deployment is created
        """

        self.env = env
        self.cluster = cluster
        
        if name is None:
            self.name = str(id(self))
        else:
            self.name = str(name)
        
        self.to_remove = 0
        
        self.nr_dead = 0 # Number of dead tasks
        self.nr_done = 0 # number of done tasks
        self.nr_err5xx = 0 # number of 5xx errors
        
        self.tasks = []    
        self.pods = []
        self.queue_length = queue_length
        
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
            self.env, self,
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
        
        # Check if pods should and can be removed
        to_remove_list = []
        for i, pod in enumerate(self.pods):
            if pod.nr_active_tasks == 0:
                if self.to_remove > 0:
                    to_remove_list.append(i)
                    self.to_remove -= 1
                    
        ### Remove unwanted pods
        for r in to_remove_list:
            if len(self.pods) > 1:
                self.pods.pop(r)
        
        # now we can start new tasks
        for pod in self.pods:
            if len(self.tasks) > 0:
                task = self.tasks[0]
                if pod.canProcess(task):
                    task = self.tasks.pop(0)
                    pod.addTask(task)
        
            
    def addTask(self, task):
        """
        Adds a task to the deployment. This task is sentto one of the 
        vacant pods, or (if all pods are busy) waits in the queue.
        """
        task.deployment = self.name
        
        if len(self.tasks)  > self.queue_length:
            self.nr_err5xx += 1
        else:
            self.tasks.append(task)
            
        self.update()
            
    def getMetrics(self):
        """
        Returns:
            nr_pods, active_pods, cpu, memory, nr_tasks, nr_done, nr_dead, nr_err5xx
            - Total number of pods
            - number of active pods (pods involved in tasks)
            - total_number of tasks
            - total cpu usage
            - total cpu capacity
            - total memory usage
            - total memoty capacity
            - number of not started tasks
            - number of done tasks (counter)
            - number of dead tasks (counter)
            - number of not accepted tasks - error 5xx (counter)
        """
        self.update()
        cpu, cpu_max = 0, 0
        memory, memory_max = 0, 0
        nr_pods = len(self.pods)
        active_pods = 0
        active_tasks = 0
        for pod in self.pods:
            if pod.nr_active_tasks > 0:
                active_pods += 1
                active_tasks += pod.nr_active_tasks
            cpu += pod.cpu
            cpu_max += pod.cpu_max
            memory += pod.memory            
            memory_max += pod.memory_max            
        return [
            nr_pods, active_pods, active_tasks, 
            np.round(cpu, 2), cpu_max, np.round(memory, 2), memory_max, 
            len(self.tasks), self.nr_done, self.nr_dead, self.nr_err5xx
        ]

    
    def taskDone(self, task):
        if not task.isAlive():
            self.nr_dead += 1
        else:
            self.nr_done += 1
            if self.cluster is not None:
                self.cluster.taskFinished(task, self)


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
        
        self.env = simpy.Environment()
        
        if pods is None:
            pods = [1] * len(durations)
            
        self.deployments = []
        for duration, pod in zip(durations, pods):
            self.deployments.append(Deployment(
                self.env,
                cluster = self,
                starting_pods = pod,
                duration_task = duration,
                cpu_base = 5,
                memory_base = 5,
            ))
        
        self.nr_tasks = 0
        self.nr_done = 0
        
        
    def addTasks(self, nr_tasks, life_time = 1e6):
        """
        Adds new tasks to the cluster. The tasks are assigned to the 
        consecutive deployments.
        Arguments:
            nr_tasks  - number of tasks to add
            life_time - life time of tasks
        """
        for i in range(nr_tasks):
            self.nr_tasks += 1
            self.deployments[0].addTask(Task(life_time = life_time))

            
    def taskFinished(self, task, deployment):
        pos = self.deployments.index(deployment) + 1
        if pos < len(self.deployments):
            self.deployments[pos].addTask(task)
        else:
            self.nr_done += 1

    def update(self, steps = 1e3):
        self.env.run(until = self.env.now + steps)
     
    def getMetrics(self):
        res = [self.nr_tasks, self.nr_done]
        for deployment in self.deployments:
            res.append(deployment.getMetrics())
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
        
            

