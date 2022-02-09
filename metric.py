import subprocess
from time import time
import pandas as pd

class Metric:
    """
        This class holds a metric object. The purpose of this object is to
        - query for metrics from the socks cluster
        - maintain and return the values
        Parameters:
            metricDF - a dtaframe with 
            timestamp - when the metrics were accessed
        Methods:
            getMetric() - returns a specific metric
    """
    def __init__(self, deployments, prom):
        """
        Arguments:
            deployments - list of deployments
            prom        - handle to prometheus connection
        """
        self.deployments = deployments
        self.prom = prom
        
        self.metricDF = self.getMetricDF()
        self.timestamp = time()
        
    
    def metricAgent2df(self, deployments = None):
        if deployments is None:
            deployments = self.deployments
        
        metrics = subprocess.run(
            ['sh'], input = './shellscripts/get_metrics.sh', 
            text=True, capture_output = True)
        metrics = [x for x in str(metrics).split('\\n') if x[:16] == 'agent_metric_res']
        
        df = pd.DataFrame()
        for i, line in enumerate(metrics):
            metric, val = line.split(' ')
            metric = [x.split('=') for x in metric[17:-1].replace('"', '').split(',')]
            for col, desc in metric:
                df.loc[i, col] = desc

            df.loc[i, 'value'] = val
            df = df[df.controlled_namespace == 'sock-shop']
            df.value = df.value.astype(float)
            df = df[df.controlled_deployment.isin(deployments)]
        return df        
        
    
    def getRequestTotal(self, deployments = None):
        if deployments is None:
            deployments = self.deployments
        req = {}
        for deployment in deployments:
            query = f'sum(irate(request_total{{direction="inbound", deployment="{deployment}"}}[5m]))'
            m = []
            while len(m) == 0:
                m = self.prom.custom_query(query=query)
            req[deployment] = float(m[0]['value'][1])
        return req

    def requestTotal2df(self, deployments = None):
        req = self.getRequestTotal(deployments)
        df = pd.DataFrame(columns = [
            'controlled_deployment', 'controlled_namespace', 'resource', 'type', 'value',
        ])
        for i, (k, v) in enumerate(req.items()):
            df.at[i, :] = [k, 'prometheus', 'request', 'total', v]
        return df

    
    def getRequestErrorsTotal(self, deployments = None):
        if deployments is None:
            deployments = self.deployments
        req = {}
        for deployment in deployments:
            query = f'sum(irate(request_errors_total{{deployment="{deployment}"}}[5m]))'
            m = []
            m = self.prom.custom_query(query=query)
            req[deployment] = float(m[0]['value'][1]) if len(m) > 0 else 0.0
        return req

    def requestTotal2df(self, deployments = None):
        req = self.getRequestTotal(deployments)
        df = pd.DataFrame(columns = [
            'controlled_deployment', 'controlled_namespace', 'resource', 'type', 'value',
        ])
        for i, (k, v) in enumerate(req.items()):
            df.at[i, :] = [k, 'prometheus', 'request', 'total', v]
        return df

    def requestErrorsTotal2df(self, deployments = None):
        req = self.getRequestErrorsTotal(deployments)
        df = pd.DataFrame(columns = [
            'controlled_deployment', 'controlled_namespace', 'resource', 'type', 'value',
        ])
        for i, (k, v) in enumerate(req.items()):
            df.at[i, :] = [k, 'prometheus', 'requesterror', 'total', v]
            
        return df
    
    def getMetricDF(self, deployments = None):
        df = self.metricAgent2df(deployments)
        df = pd.concat([df, self.requestTotal2df(deployments)], ignore_index = True)
        df = pd.concat([df, self.requestErrorsTotal2df(deployments)], ignore_index = True)
        df.columns = ['deployment', 'namespace', 'resource', 'metrictype', 'value']
        return df
    
    def getMetric(self, resource, deployment = None, metrictype = None):
        if deployment is None:
            deployment = self.deployments[0]
        
        tmp = self.metricDF[(self.metricDF.deployment == deployment)]
        tmp = tmp[tmp.resource == resource]
        if resource in ('request', 'requesterror'):
            return tmp.value.iloc[0]
        
        if metrictype is None:
            metrictype = 'usage'
        
        return tmp[tmp.metrictype == metrictype].value.iloc[0]