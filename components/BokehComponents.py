from datetime import date,datetime,timedelta
from random import randint
from bokeh.io import output_file, show
from bokeh.layouts import widgetbox, Spacer
from bokeh.models import ColumnDataSource,CustomJS,Div
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn, Tabs, Panel
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider
from bokeh.layouts import row
from bokeh.plotting import figure
from bokeh.io import show, output_notebook
from bokeh.layouts import layout
from bokeh.events import ButtonClick
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
import pandas as pd
import pandas_datareader as pdr
from bokeh.plotting import figure,show,output_file

class BokehTableComponent():
    def __init__(self,settings=None):
        self._settings = {}
        if settings:
            self._settings = settings

        [data,id_field] = self.initData()
        self.id_field = id_field
        self.data = data
        #self.hooks= {'select':[],'delete':[],''}
    
    def setDataAndRefresh(self,data):
        self.data = data
        if( self.source):
            self.source.data = data
            
    def getData(self):
        return self.data
    
    
    def getBokehComponent(self):
        ## First, we construct the data source
        if self.data is None:
            self.data = {}
        source = ColumnDataSource(self.data)
        source.selected.on_change('indices', self.getCallback())        
        #source.on_change('selected', callback_in)
        columns = []
        for k in self.data.keys():
            columns.append(TableColumn(field=k, title=k))
            #TableColumn(field="dates", title="StartDate", formatter=DateFormatter()),
        data_table = DataTable(source=source, columns=columns, width=900, height=280)
        
        # assign class variables
        self.data_table = data_table
        self.source = source
        return self.data_table
    
    def getSelected(self):
        s = self.source.selected.indices
        return s

    def doRemoveIndices(self,selected_index):
        for k in self.data.keys():
            self.data[k].pop(selected_index)
        return True

    def doDataUpdate(self):
        return True

    def removeIndices(self,selected_index):
        if self.doRemoveIndices(selected_index):
            return True
        return False

    def removeSelected(self):
        try: 
            l = len(self.source.selected.indices)
        except:
            print("CRITICAL ERROR in removeSelected")
            print(self._settings)
            display(self.source)
            display(self.source.selected)
            display(self.source.selected.indices)

        if l == 0:
            self.source.selected.indices = []
            return
        selected_index = self.source.selected.indices[0]
        self.removeIndices(selected_index)
        self.doDataUpdate()
        self.setDataAndRefresh(self.data)
        self.source.selected.indices = []

    ## Event Handles
    # Call me when you get a selection event on the resulting table
    def handle_select_callback(self,attr, old, new):

        indices = [self.data[self.id_field][i] for i in new ]
        self.source.selected.indices = new
        self.do_handle_select(attr,old,new)

    def do_handle_select(self,attr,old,new):
        pass
    
    def Class(self):
        classobj= globals()[self.__class__.__name__]
        return classobj

    def getCallback(self):
        return self.handle_select_callback

    def registerHook(action,function):
        pass
    ####### 
    # Global Interface that needs to be updated whenever inheritance happens
    #
    #
    #
    def initData(self):
        data = {
            'theid':['demo_'+str(i) for i in range(10)],
            'dat':['data data ' for i in range(10)],
            }
        id_field = 'theid'
        return [data,id_field]
    


class BokehControl():
    def __init__(self,settings=None):
        self._settings = settings
        if settings == None:
            self._settings = {}

class BokehButton(BokehControl):
        
    def getBokehComponent(self):
        self.bk = Button(label=self._settings['label'])
        self.bk.on_event(ButtonClick, self.handle_click)
        return self.bk
    
    def handle_click(self,event):
        raise Exception ("Should not be creating a general button")



class BokehSelect(BokehControl):
        
    def getBokehComponent(self):
        self.select = Select(title=self._settings['title'], 
                             value=self._settings["value"], 
                             options=self._settings['options'])

        return self.select
    
    def handle_select(self,event):
        raise Exception ("Should not be creating a general button")


class QueryTableComponent(BokehTableComponent):
    def initData(self):
        self.pi = self._settings['buffered_query_interface']
        data = self.pi.QueryData()
        id_field = self._settings['id_field']
        return [data,id_field]
    
    __instance = None
    
    def doRemoveIndices(self,index):
        idval = self.data[self.id_field][index]
        self.pi.DoAction(action_id = 'kill', query={'key':self.id_field,'value':idval} )
        return True

    def doDataUpdate(self):
        self.data = self.pi.QueryData()
        return True    



import pandas as pd

class BufferedQueryInterface():
    '''
    QueryTableComponent(BokehTableComponent) ----> BufferedQueryInterface
    The buffered Query Interface can be used by a BokehTableComponent to handle data. The BokehTable handles events, and front-end concerns. The Query Interface handles data, and all query concerns. It is possible to inherit from, and oveerride the Buffered Query Interface to support a wide variety of queries. These can be to MongoDB, to SQLite, to flat files.
    '''
    def __init__(self):
        self.load_data_buffer()

    def QueryIndices(self,query=None):
        '''
        Find the indices that result from executing any query.
        '''
        self.load_data_buffer()

        L = list(self.data.keys())

        if len(L)==0:
            return []

        if query:
            if 'key' in query and 'value' in query:
                lst = self.data[query['key']]
                indices = [i for i, x in enumerate(lst) if x == query['value']]
                return indices
            else:
                k = list(self.data.keys())[0]
                return [i for i in range(0,len(self.data[k]))]
        else:
            k = list(self.data.keys())[0]
            return [i for i in range(0,len(self.data[k]))]
    
    def QueryData(self,query=None):
        '''
        Find the data rows that corrispond with any query.
        '''
        self.load_data_buffer()
        indices = self.QueryIndices(query)
        if indices:
            ret_data = {}
            for k in self.data:
                ret_data[k] = [self.data[k][i] for i in indices]
            return ret_data
        return None
    def DoAction(self,action_id = None,query=None):
        '''
        Try to execute any user defined action.
        '''        
        if action_id not in self.actions.keys():
            raise Exception("Encountered illegial action request in " + str(self) + " with action " + action_id )
        action_func = self.actions[action_id]
        indices = self.QueryIndices(query)
        action_func(indices)
        self.load_data_buffer()

    #### Interface below -- Should be overriden by data sources
    #
    #
    #
    #
    def load_data_buffer(self):
        self.data = {
            'process_id':[str(i) for i in range(100)],
            'file':['jobStatrer_'+ str(i%3) for i in range(100)],
            'memory':[ i for i in range(100)],
            'cpu':[ i for i in range(100)],
            }
        self.actions = {'kill':self.action_kill}
    
    
    def action_kill(self,ids):
        for k in self.data.keys(): 
            for selected_index in reversed(ids):
                self.data[k].pop(selected_index)
      