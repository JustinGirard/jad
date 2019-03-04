

import sys
sys.path.append('../../')

import datetime
import pandas_datareader as pdr

from bokehComponents.Dashboard import Dashboard
from bokehComponents.BokehComponents import BufferedQueryInterface,QueryTableComponent,InteractiveDataGroup,LoadButton
from bokehComponents.BokehComponents import ActionButton,BokehTimeseriesGraphic,BokehButton,ExperimentTable,BokehControl
from jad.dashboards.DataQueries import AutotradeAPIQuery


from bokeh.io import output_notebook,output_file
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models.widgets import Panel, Tabs,TextInput #, DataTable, DateFormatter, TableColumn, Tabs, 
from bokeh.layouts import layout
from bokeh.plotting import figure,show,output_file
from bokeh.models import Div
from conf.conf import conf
from conf.conf import objectConf
import requests


class BokehText(BokehControl):
    def doInit(self):
        pass
    def regiserHooks(self):
        pass
    def handle_on_change(self,attr, old, new):
        for trg in self._settings['datasource_targets']:
            ## The id we are using must match one of the published filters for the target datasoruce
            try:
                assert self._settings['id_field'] in trg.get_filter_keys()
                lst = list(trg.get_filter_keys())
                arg = {lst[0]:new}
                print("LOADING...")            
                trg.DoAction(action_id = 'set_filter',argument=arg)
            except   Exception as e:
                import traceback
                traceback.print_exc()
                raise e

    def getBokehComponent(self):
        text = TextInput(value='', title=self._settings['label'])
        text.on_change('value', self.handle_on_change)
        return text

class APITestConsole(Dashboard):        
    def getControlArea(self):
        visuals = []
        #button_defs = [{'label':'Send Welcome','action':'sent_welcome','class':SendWelcomeEmail,'datasource_id':'clients','selection':True}]
        button_defs =[{'label':'Enter your API key, press enter', 'action':'refresh','class':BokehText,'datasource_id':'clients'}]
        datasources = []

        datasources.append({'class':AutotradeAPIQuery,
                        'datasource_id':'clients'})

        visuals.append({'class':ExperimentTable,
                        'width':800,
                        'height':300,
                        'date_keys':[],
                        'title':"API Test Response",
                        'hide':[],
                        #'q_key':'status',
                        #'q_value':'running',
                        #'q_operator':'=',
                        'datasource_id':'clients'
                       })

        self.dw = InteractiveDataGroup({'datasources':datasources,
                        'visuals':visuals,
                        'commands':button_defs,
                        'datasource_targets':{'clients':'clients'}
                        })    
        
        layoutList = []
        layoutList.append(self.getConsole([self.dw]))
        return layout(layoutList, sizing_mode='fixed')
    
    def getLayout(self):
        return self.getControlArea()
