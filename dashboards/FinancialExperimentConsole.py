
tasks = """
Software Development: (Friday)
##################################
0) Plan Software mMarketing. Representworkflow 
1) MergeDashboards
2) Order Properties Browser 
3) Loading and Submit Experiments
4) Alerts and notifications can be scheduled and hooked into code via log function with logging decorator
5) Simplify pull of financial data from Process Handle
) Automated Source Control Integration




1) Buffered Financial History prepared by the running algorithm
-----------
--- for paper trades
--- for algotrades inserts
--- orders are saved with dictionary
--- backtest / and running data versions
--- memory consumption
--- iteration time

2) Graphs:
------------
--- Backtest: value_total and algotrades
--- Paper Trade: value_total and algotrades

3) Whole system (Top and bottom) Do periodic updates, constantly.

Visual Update (Thursday)
#############################
3) See last weeks algotrades
4) Algorithms Displayed:
--- experiment_id
--- codebase version
--- proper name
--- profit/loss
--- value_total
5) time rows
--- last contact
--- MarketExperiment iteration
--- last paper trade

6) Add current orders into under table
7) fix button alignment
"""

import sys
sys.path.append('../../')

import datetime
import pandas_datareader as pdr

from bokehComponents.Dashboard import Dashboard
from bokehComponents.BokehComponents import BufferedQueryInterface,QueryTableComponent,InteractiveDataGroup,LoadButton
from bokehComponents.BokehComponents import ActionButton,BokehTimeseriesGraphic,BokehButton,ExperimentTable,BokehLogDiv
from jad.dashboards.DataQueries import AlgorithmQuery, MarketDataFacade,AutotradePerformanceTimeseries,JefSystemOut,JefFileText


from bokeh.io import output_notebook,output_file
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models.widgets import Panel, Tabs #, DataTable, DateFormatter, TableColumn, Tabs, 
from bokeh.layouts import layout
from bokeh.plotting import figure,show,output_file
from bokeh.models import Div
from conf.conf import conf
from conf.conf import objectConf

#visuals.append({'class':ExperimentTable,
#                        'width':800,
#                        'datasource_id':'timeseries',
#                        'height':600,
#                        'date_keys':['date'],
#                        'title':"Backtest Rows",
#                        'hide':['value','pl_value','date','experiment_id','cost','sharesAmount','amount']
#                      })        
class LoadExperiment(ActionButton):
    def handle_selection(self,event,ids,idfields):
        #print(self._settings)
        #print(ids)
        #print(idfields)
        ei = ExperimentInterface()
        link = ei.GetExperimentConsoleTarget(ids[0])
        from IPython.core.display import HTML
        print(HTML("<a href='"+link +"'>Edit '"+ids[0]+"' Here</a>"))

class FinancialExperimentConsole(Dashboard):    
    
    
    def getControlArea(self):
        mdf = MarketDataFacade()


        #######################
        #
        # Backtest Performance
        #
        
        visuals = []
        button_defs = []
        datasources = []
        datasources.append({'class':AutotradePerformanceTimeseries,'market_data':mdf,'datasource_id':'timeseries'})                         
        visuals.append({'class':BokehTimeseriesGraphic,
                                'title':'Backtest Profit Loss',
                                'width':800,
                                'height':400,
                                'datasource_id':'timeseries',
                                'data_defs':[{'y':'pl_value',
                                             'x':'date',
                                             'key':'profit',
                                             'label':'ProfitPercent',
                                             'color':'black' }]
                                })
        
        
        visuals.append({'class':BokehTimeseriesGraphic,
                                'title':'Backtest Paper Trading',
                                'datasource_id':'timeseries',
                                'width':800,
                                'height':400,
                                'data_defs':[{'y':'value',
                                             'x':'date',
                                             'key':'profit',
                                             'label':'Account Value',
                                             'color':'black' }]
                                })

                
        self.backtest = InteractiveDataGroup({'datasources':datasources,
                'visuals':visuals,
                'commands':button_defs,
                })    

        #######################
        #
        # Present Performance
        #
        
        visuals = []
        button_defs = []
        datasources = []
        datasources.append({'class':AutotradePerformanceTimeseries,
                            'market_data':mdf,
                            'datasource_id':'rttime',
                            'mode':'realtime'})                         
        visuals.append({'class':BokehTimeseriesGraphic,
                                'title':'Live Profit Loss',
                                'width':800,
                                'height':400,
                                'datasource_id':'rttime',
                                'data_defs':[{'y':'pl_value',
                                             'x':'date',
                                             'key':'profit',
                                             'label':'ProfitPercent',
                                             'color':'black' }]
                                })
        
        
        visuals.append({'class':BokehTimeseriesGraphic,
                                'title':'Live Paper Trading',
                                'datasource_id':'rttime',
                                'width':800,
                                'height':400,
                                'data_defs':[{'y':'value',
                                             'x':'date',
                                             'key':'profit',
                                             'label':'Account Value',
                                             'color':'black' }]
                                })
        
        self.paper = InteractiveDataGroup({'datasources':datasources,
                'visuals':visuals,
                'commands':button_defs,
                })            
        
        
        #######################
        #
        # System Output
        #
        button_defs = []
        datasources = [{'class':JefSystemOut,'market_data':mdf,'datasource_id':'sysout'}]                         
        visuals =[{'class':BokehLogDiv,'title':'System Output','width':800, 'height':400,'datasource_id':'sysout',
                                'data_field':'system_out','display_range':100}]
        self.systemout = InteractiveDataGroup({'datasources':datasources,'visuals':visuals,
                'commands':button_defs,'filter':None,}) 

        #######################
        #
        # File Download
        #
        button_defs = []
        datasources = [{'class':JefFileText,'market_data':mdf,'datasource_id':'expcode'}]                         
        visuals =[{'class':BokehLogDiv,'title':'Experiment Code','width':800, 'height':400,'datasource_id':'expcode',
                                'data_field':'file','display_range':100,'type':'textarea'}]
        self.expcode = InteractiveDataGroup({'datasources':datasources,'visuals':visuals,
                'commands':button_defs,}) 

        
        
        ###############################
        #
        # Top Pane
        #
        
        visuals = []
        button_defs = []
        datasources = []
        
        datasources.append({'class':AlgorithmQuery,
                        'market_data':mdf,
                        'datasource_id':'algselect'
                        })
        visuals.append({'class':ExperimentTable,
                        'width':800,
                        'height':300,
                        'date_keys':['last_contacted','current_date'],
                        'title':"Running Algorithms",
                        'hide':[],
                        'q_key':'etype',
                        'q_value':'experiment',
                        'q_operator':'=',
                        'datasource_id':'algselect'
                       })



        #visuals_detail.append({'class':BokehDiv,'width':800,'height':200,'title':"System Out"})
        
        button_defs.append ({'class':ActionButton,'action':'halt','label':'Halt Selected','datasource_id':'algselect','selection':True})
        button_defs.append ({'class':ActionButton,'action':'auto_on','label':'Autostart','datasource_id':'algselect','selection':True})
        button_defs.append ({'class':ActionButton,'action':'auto_off','label':'No Autostart','datasource_id':'algselect','selection':True})
        button_defs.append ({'class':ActionButton,'action':'tracememory_on','label':'Trace Memory','datasource_id':'algselect','selection':True})
        button_defs.append ({'class':ActionButton,'action':'tracememory_off','label':'No Trace Memory','datasource_id':'algselect','selection':True})
        button_defs.append ({'class':LoadButton,'action':'set_experiment','label':'Load Algorithm','datasource_id':'algselect','selection':True})
        button_defs.append ({'class':LoadExperiment,'label':'Edit Algorithm','datasource_id':'algselect','action':'load_experiment','selection':True})
        
        dst = {}
        dst.update(self.backtest.getDatasources())
        dst.update(self.paper.getDatasources())
        dst.update(self.systemout.getDatasources())
        dst.update(self.expcode.getDatasources())
        
        self.dw = InteractiveDataGroup({'datasources':datasources,
                        'visuals':visuals,
                        'commands':button_defs,
                         'datasource_targets':dst, #This is the group that any selection filters
                        })    
        #loadExp =  LoadExperiment({'label':"Load Experiment"})
        layoutList = []
        layoutList.append(self.getConsole([self.dw]))
        layoutList.append(self.getConsole([self.backtest,self.paper,self.systemout,self.expcode]))
        #layoutList.append(loadExp.getBokehComponent())
        
        
        return layout(layoutList, sizing_mode='fixed')

    def getConsole(self,dataGroupList):
        # Include panels as tabs
        visual_components = []
        button_components = []
        for dataGroup in dataGroupList:
            for visual in dataGroup.getVisuals():
                title = "add title:'Default' to"
                if 'title' in visual._settings:
                    title = visual._settings['title']
                panel = Panel(child=visual.getBokehComponent(), title=title)
                visual_components.append(panel)

            for buttonInstance in dataGroup.getControls():
                button= buttonInstance.getBokehComponent()
                button_components.append(button)

        tabs = Tabs(tabs=visual_components, width=500) 
        return layout([tabs,layout(button_components)])
                
            
    def getLayout(self):
        return self.getControlArea()


import sys
import pandas as pd
from pymongo import MongoClient
sys.path.append('../../')
from conf.conf import objectConf
from conf.conf import conf
from jad.dashboards.DataQueries import MarketDataFacade

class ExperimentInterface:
    def __init__(self):
        self.experiment_launcher_conn = conf.get( "experiment_launcher_conn", '' )
        print(self.experiment_launcher_conn )
        self.retPath = conf.get('jad_console_path',"http://dev.paxculturastudios.com:9999/notebooks/jad/roughNotebooks/ExperimentLoaderClassDevelopment.ipynb")
        console_id = conf.get('jad_console_id',"dev.paxculturastudios.com")
        self.op_console = objectConf(self.experiment_launcher_conn)
        self.op_console.setKey({'console_id':console_id})
        self.op_console.load()

    def Setup(self,eid):
        self.op_console.setSetting('experiment_target',eid)
        self.op_console.save()
        return self.retPath
        
    def LoadExperiment(self,name="default"):
        #
        # Load Experiment Id
        #
        eid = self.op_console.getSetting('experiment_target')
        return eid