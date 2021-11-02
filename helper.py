### This file contains some helper functions that are used for testing and visualization purposes
import pandas as pd
import matplotlib.pyplot as plt

def dic2DF(dic):
    """
    Changes a dictionary with metrics into Pandas dataframe 
    """
    
    def unravel_column(df, colname):
        """
        A helper function that unravels a list of metrics into separate DF columns
        """
        df2 = pd.DataFrame(df[colname].tolist(), index= df.index)
        cols = ['pods', 'activePods', 'activeTasks', 'cpu', 'cpu_max', 'memory', 'memory_max', 'queueTasks', 'nrDone', 'nrDead', 'nrErr5xx']
        cols = [f'{colname}_{x}' for x in cols]
        df2.columns = cols
        df = pd.concat([df, df2], axis=1).drop(colname, axis=1)
        return df
    
    df = pd.DataFrame.from_dict(dic, orient='index')
    df.columns = ['totalTasks', 'totalDone', 'dep1', 'dep2', 'dep3']
    for i in range(1, 4):
        df = unravel_column(df, f'dep{i}')
    return df


def plotDeploymentData(df, sufix = 'pods', legend = None):
    """
    Plots a selected metric for each deployment separately 
    Arguments:
        df     - dataframe prepared by dic2DF function
        sufix  - name of the metric (corresponds to column names 
                 from df)
        legend - legend to be displayed. If None, a standard
                 legend is displayed
    """
    cols = [x for x in df.columns if x[-len(sufix):] == sufix]
    df[cols].plot()
    plt.title(sufix)
    if legend is not None:
        plt.legend(legend)
    plt.xlabel('milicroseconds')

def plotDeploymentDataSum(df, sufix = 'pods'):
    """
    Summarises a selected metric over a deployment and plots it 
    Arguments:
        df     - dataframe prepared by dic2DF function
        sufix  - name of the metric (corresponds to column names 
                 from df)
    """    
    cols = [x for x in df.columns if x[-len(sufix):] == sufix]
    tmp = df[cols].copy()
    tmp[sufix] = tmp[cols].sum(axis=1)
    tmp[[sufix]].plot()
    plt.title(f'{sufix} (total)')
    plt.legend('')
    plt.xlabel('miliseconds')


def plotTasks(df):
    """
    Plots the number of tasks
    Arguments:
        df     - dataframe prepared by dic2DF function
    """
    
    sufix = 'nrDone'
    cols = [x for x in df.columns if x[-len(sufix):] == sufix]
    tmp = df[[cols[-1]]].copy()
    #tmp[sufix] = tmp[cols].sum(axis=1)
    tmp['received'] = df['totalTasks']
    tmp = tmp[['received', cols[-1]]]
    tmp.columns = ['received', 'finished']
    tmp.plot()    
    plt.title('Number of tasks')
    plt.xlabel('miliseconds')
    
def plotClusterHistory(df):
    """
    Creates a series of plots that show the entire history of a cluster
    Arguments:
        df     - dataframe prepared by dic2DF function
    """    
    plotDeploymentData(df)
    plotDeploymentData(df, 'activePods', legend='')
    plotDeploymentData(df, 'activeTasks', legend='')
    plotDeploymentData(df, 'queueTasks', legend='')
    plotDeploymentDataSum(df, 'cpu')
    plotDeploymentData(df, 'cpu', legend='')
    plotDeploymentData(df, 'nrDone', legend='')
    plotDeploymentData(df, 'nrErr5xx', legend='')
    plotTasks(df)
    