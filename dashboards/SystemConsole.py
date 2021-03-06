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
from BokehComponents import *
try:
    from jef.experiment_manager import experiment_manager
except:
    from jef.jef.experiment_manager import experiment_manager
from conf.conf import conf

class ProcessQuery(BufferedQueryInterface):
    def load_data_buffer(self):
        if hasattr(self, 'data'):
            pass
        else:
            self.data = {
                'process_id':[str(i) for i in range(100)],
                'file':['process_name' for i in range(100)],
                'memory':[ i%10+10 for i in range(100)],
                'cpu':[ i%5+10 for i in range(100)],
                }
            self.actions = {'kill':self.action_kill}
    
    def action_kill(self,ids):
        for k in self.data.keys(): 
            for selected_index in reversed(ids):
                self.data[k].pop(selected_index)

class ExperimentManagerInterface:
    
    _em = None
    
    @staticmethod
    def getDataGrid(type_id='experiment',id_field='eid'):
        if ExperimentManagerInterface._em is None:
            ExperimentManagerInterface._em=experiment_manager( mongo_server = conf.get( 'jef_mongo_host', '54.214.220.236' ),
                                    port = conf.get( 'jef_mongo_port', 27017 ),
                                    mongo_db = conf.get( 'jef_mongo_db', 'fleetRover' ),
                                    username = conf.get( 'jef_mongo_username', 'pax_user' ),
                                    password = conf.get( 'jef_mongo_password', 'paxuser43' ),
                                    authSource = conf.get( 'jef_mongo_authSource', 'fleetRover' ) )

                            
        df=ExperimentManagerInterface._em.listexpts(status=['running'],query={'settings.experiment_type':type_id})
        L = len(df.index)
        #print(type_id)
        #print(L)
        #print(df.to_string())

        if L==0:
            return {}
        data = {
                id_field:[ df.loc[i,'experiment_id'] for i in range(L)],
                'name':[ df.loc[i, 'name'] for i in range(L)],
                'status':['running ' for i in range(L)],
                'duration':[0 for i in range(L)],
                }                   
        return data
        
class ExperimentQuery(BufferedQueryInterface):
 
    def load_data_buffer(self):
 
        self.data = ExperimentManagerInterface.getDataGrid(type_id="experiment",id_field="eid")    
        self.actions = {'kill':self.action_kill}
    
    def action_kill(self,ids):
        print(ids)
        print(self.data)
        for k in self.data.keys(): 
            for selected_index in reversed(ids):
                self.data[k].pop(selected_index)

                
class AlgorithmQuery(BufferedQueryInterface):
    def load_data_buffer(self):
        
        self.data = ExperimentManagerInterface.getDataGrid(type_id="algorithm",id_field="aid")    
        self.actions = {'kill':self.action_kill} 
    
    def action_kill(self,ids):
        print(ids)
        print(self.data)
        for k in self.data.keys(): 
            for selected_index in reversed(ids):                
                self.data[k].pop(selected_index)     

class TimeseriesGraphic(BokehControl):
    
    def setPlotData(self):    
        
        start_init=datetime(2017,1,26)
        end_init=datetime(2017,4,26)
        try:
            self.day_delta = self.day_delta + 1
        except:
            self.day_delta = 0

        # Grab data
        start=start_init + timedelta(days=self.day_delta)
        end=end_init + timedelta(days=self.day_delta)

        data=pdr.get_data_yahoo('AAPL',start,end)
        data_sorted=data.sort_index(axis=0,ascending=True)
        date_list=list(data_sorted.index)

        # Save the data elements
        self.open_list=list(data_sorted['Open'])
        self.close_list=list(data_sorted['Close'])
        self.date_time=[datetime.strptime(str(d),'%Y-%m-%d %H:%M:%S').date() for d in date_list]
        try:
            self.ds1.data['x'].append(self.date_time[len(self.date_time)-1])
            self.ds1.data['y'].append(self.open_list[len(self.date_time)-1])
            self.ds2.data['x'].append(self.date_time[len(self.date_time)-1])
            self.ds2.data['y'].append(self.close_list[len(self.date_time)-1])
            self.ds1.trigger('data', self.ds1.data, self.ds1.data)
            self.ds2.trigger('data', self.ds2.data, self.ds2.data)  
            
        except Exception as e:
            print(e)

    def getFinancePlot(self):

        self.setPlotData()


        p=figure(x_axis_type='datetime',plot_width=500,plot_height=500,title="Financial Analysis",tools="",
                      toolbar_location=None)

        #p.circle(date_time,open_list,legend="Open Price",size=6,color="green", alpha=0.5)
        r1 = p.line(self.date_time,self.open_list,legend="Open Price",color="green", alpha=0.5)
        #p.circle(date_time,close_list,legend="Close Price",size=6,color="red", alpha=0.5)
        r2 = p.line(self.date_time,self.close_list,legend="Close Price",color="red", alpha=0.5)
        p.legend.location = "bottom_right"

        self.ds1 = r1.data_source
        self.ds2 = r2.data_source

        b = Button(label="Refresh")
        #b.on_event(ButtonClick, FinancialConsole.callback_refresh_analytics)
        l = layout([p,b])


        return(l)    
    
    def getBokehComponent(self):
        return self.getFinancePlot()
    
    def callback_refresh_analytics(self,event=None):
        self.setPlotData()



#---------------------- Console


output_notebook()
output_file("data_table.html")
class FinancialConsole:
    def __init__(self):
        self.div = Div(width=300)
        self.pt  = ProcessTableComponent()        
        self.et  = ExperimentTableComponent()        
        self.b_kill = KillButton({'tables_to_kill':[self.pt,self.et],'label':'kill'})
        self.b_show = ShowButton({'label':'show'})
        self.b_restart = ShowButton({'label':'restart'})
        self.time_graphic = TimeseriesGraphic()
        self.periodicCallbacks = [self.time_graphic.callback_refresh_analytics]
        
        self.s_adviceSelect = BokehSelect({'title':"Advice On:", 'value':"Auto", 'options':["Yes", "No", "Auto"]})
        self.s_tradeSelect = BokehSelect({'title':"Trade:", 'value':"Auto", 'options':["Yes", "No", "Auto"]})
        self.s_autoRestart = BokehSelect({'title':"Autostart:", 'value':"No", 'options':["Yes", "No"]})
        
    def getPeriodicCallbacks(self):
        return self.periodicCallbacks
        
    def getControlPanel(self):
        
        bk = self.b_kill.getBokehComponent()
        br = self.b_restart.getBokehComponent()
        bs = self.b_show.getBokehComponent()
        adviceSelect = self.s_adviceSelect.getBokehComponent()
        tradeSelect  = self.s_tradeSelect.getBokehComponent()
        autoRestart  = self.s_autoRestart.getBokehComponent()
        
        c_tab1 = Panel(child=layout([bk,bs,br], sizing_mode='fixed'),title="Commands")
        c_tab2 = Panel(child=layout([adviceSelect,tradeSelect,autoRestart], sizing_mode='fixed'),title="Signals")
        c_tabs = Tabs(tabs=[ c_tab1,c_tab2], width=300)
        
        return widgetbox(c_tabs)
    


    def getConsole(self):

        self.analytics_div = Div(text="""Analytics HTML""", width=200, height=100)
        self.console = Div(text="""System Out console:""", width=200, height=100)
        #(Compute Nodes, Running Experiments, Queue and History, Orders & Advice )
        financePlot = self.time_graphic.getBokehComponent()

        j_tab1 = Panel(child=layout([financePlot], sizing_mode='fixed'),title="Analytics")
        j_tab2 = Panel(child=layout([Div(height=500,width=500)], sizing_mode='fixed'),title="System Out")
        j_tab3 = Panel(child=layout([Div(height=500,width=500)], sizing_mode='fixed'),title="Log Data")
        j_tab4 = Panel(child=layout([Div(height=500,width=500)], sizing_mode='fixed'),title="Job Code")
        j_tabs = Tabs(tabs=[ j_tab1, j_tab2, j_tab3, j_tab4 ], width=700)

        
        l1 = layout([
          [
            [self.pt.getBokehComponent()]         
          ],
           [self.getControlPanel()],
            [self.console]            
        ],sizing_mode='fixed')         
        
        l2 = layout([
          [
            [self.et.getBokehComponent()],
                Spacer(width=20),
           []          
          ],
           [self.getControlPanel(),j_tabs],
            [self.analytics_div]
           ,
        ],sizing_mode='fixed') 
        

        tab1 = Panel(child=l1,title="System Processes")
        tab2 = Panel(child=l2,title="Running Experiments")
        tab3 = Panel(child=Div(height=300,width=600),title="Orders & Integration")
        tabs = Tabs(tabs=[ tab1, tab2, tab3 ])
        return tabs
    
# Create the Document Application
global fd,ee
def modify_doc(doc):
    
    # Create the main plot
    def create_figure():
        global fd,ee        
        ee = FinancialConsole()
        return ee.getConsole()
    
    # Update the plot
    def update(attr, old, new):
        print('test')
    
    doc.add_root(create_figure())
    pc_list = ee.getPeriodicCallbacks()
    for callback in pc_list:
        doc.add_periodic_callback(callback, 500)

def showConsole(    notebook_url="ec2.paxculturastudios.com:9999"):
    app = Application( FunctionHandler(modify_doc))
    doc = app.create_document()
    show(app, notebook_url=notebook_url)