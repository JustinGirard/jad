import sys
sys.path.append('../../')

import datetime
import pandas_datareader as pdr

from bokehComponents.Dashboard import Dashboard
from bokehComponents.BokehComponents import BokehControl,BufferedQueryInterface,QueryTableComponent,BokehTimeseriesGraphic,BokehButton
from bokehComponents.BokehComponents import ExperimentTable,BokehControl,ActionButton,LoadButton,InteractiveDataGroup,BokehDiv

from bokeh.io import output_notebook,output_file
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models.widgets import Panel, Tabs #, DataTable, DateFormatter, TableColumn, Tabs, 
from bokeh.layouts import layout
from bokeh.plotting import figure,show,output_file
from bokeh.models import Div
from conf.conf import conf
from conf.conf import objectConf
import pandas as pd
from jef.jef.experiment_manager import experiment_manager
import sys
sys.path.append('../../')

import pymongo
import random


from financialNodes import MarketExperiment

#
#
# Database details && EM
#

class MarketDataFacade():
    facade = None
    def __init__(self, securities=None, start_date=None,end_date=None,cash=None,experiment_id=None):
        if securities:
            self.me = MarketExperiment(securities,
                               start_date,
                               end_date,
                               cash,
                               'minute')
            self.me.context['experiment_id'] = experiment_id

        host=conf.get("jef_mongo_host")
        port=conf.get("jef_mongo_port")
        dbname=conf.get("jef_mongo_db")
        username=conf.get("jef_mongo_username")
        password=conf.get("jef_mongo_password")
        authSource=conf.get("jef_mongo_authSource")

        import pandas as pd
        self.em = experiment_manager(mongo_server=host,mongo_db=dbname,port=port,username=username,password=password,authSource=authSource)

    def getMe(self):
        return self.me

    def getEm(self):
        return self.em

import pymongo
import random

#cur = client.advice.autotrades.find({'experiment_id':'autotrading-20190109-611374fc-1434-11e9-bd04-062b1b6fe204'})
#df = pd.DataFrame(autotrades)
import pymongo


#
#
# Query the processes (either running, or past), and perform actions on those processes
#

class AlgorithmQuery(BufferedQueryInterface):


    def do_init(self):
        #
        ## First, create the data
        self.data = {
            'experiment_id':[],
            'last_contacted':[],
            'name':[],
            'etype':[],
            'status':[],
            'auto_restart':[],
            'expmpde':[],
            }      
        #self.registerAction('addOrder' ,OrderQuery.addOrder, "Add an order into the simulation", "None")
        #self.registerAction('closeOrder' ,OrderQuery.closeOrder, "Close out the position of an order",['TYPE_INDICES'])
        self.registerId('experiment_id',"The field that uniquely describes an experiment")
        self.registerFilter(filter_id='etype',default=None,description="The type of experiment")
        self.em = self._settings['market_data'].getEm()
        self.registerAction('append',AlgorithmQuery.appendNextAction)
        self.registerAction('halt',AlgorithmQuery.deleteAction)
        self.registerAction('auto_off',AlgorithmQuery.autoOff)
        self.registerAction('auto_on',AlgorithmQuery.autoOn)

        self.registerAction('testmode_off',AlgorithmQuery.testmodeOff)
        self.registerAction('testmode_on',AlgorithmQuery.testmodeOn)
        self.registerAction('tracememory_off',AlgorithmQuery.tracememoryOff)
        self.registerAction('tracememory_on',AlgorithmQuery.tracememoryOn)
    '''
        Get realtime stock data, and handle orders
    '''

    def getInternalAlgorithmStatus(self,status_in):
        op = objectConf(self.exp_conn)
        rec = op.find({'status':status_in})
        status = {}
        for r in rec:
            x = r
            x['_id'] = str(x['_id'])
            status[x['experiment_id']] = x
        return status
            
    
    def appendNextAction(self,indicesIn= None):
        #
        ## First, you are given selected data indices. Sometimes this may be null. in this action we will ignore this index.
        return
        assert indicesIn or not indiciesIn # do something with indices if you want

        #
        ## Second, do something with self.data

        next_day = self.current_date+ timedelta(days=3)
        data=pdr.get_data_yahoo('AAPL',self.current_date,next_day)
        self.data['open_list'].append(data['Open'][0])
        self.data['close_list'].append(data['Close'][0])
        self.data['date_time'].append(next_day)
        assert len(self.data['open_list']) == len(self.data['close_list'])
        assert len(self.data['close_list']) == len(self.data['date_time'])

        self.current_date = next_day 
    
    def __getTargetIds(self,indicesIn):
        indicesIn.sort(reverse=True)
        experiment_ids = []
        for i in indicesIn:
            #for tableName in self.data.keys():
                #self.data[tableName]
            experiment_ids .append(self.data['experiment_id'][i])
        return experiment_ids
        
    def deleteAction(self,indicesIn= None):
        experiment_ids = self.__getTargetIds(indicesIn)
        print("Deleting",str(experiment_ids))
        for experiment_id in experiment_ids:
            self.em.halt(experiment_id=experiment_id)
    
    
    def baseToggle(self,key,status,indicesIn):
        assert indicesIn
        experiment_ids = self.__getTargetIds(indicesIn)
        print(key + " set to " + str(status) ,str(experiment_ids))
        for experiment_id in experiment_ids:
            for conn in [self.exp_conn,self.exp_prop]:
                op = objectConf(conn )
                op.setKey({'experiment_id':experiment_id})
                op.setSetting(key,status)
                res = op.save()
                obj = op.load()
    
    def autoOn(self,indicesIn= None):
        self.baseToggle('auto_restart',True,indicesIn)
    def autoOff(self,indicesIn= None):
        self.baseToggle('auto_restart',False,indicesIn)

    def testmodeOff(self,indicesIn= None):
        self.baseToggle('test_mode',False,indicesIn)
    def testmodeOn(self,indicesIn= None):
        self.baseToggle('test_mode',True,indicesIn)

    def tracememoryOff(self,indicesIn= None):
        self.baseToggle('trace_memory',False,indicesIn)
    def tracememoryOn(self,indicesIn= None):
        self.baseToggle('trace_memory',True,indicesIn)
                    
    def loadAdditionalData(self,keys,connection):
        # Load Job Properties
        jp = JefPropertiesReader({'connection':connection})
        prop_keys = keys
        jp.DoAction(action_id='set_filter',argument={'fields':prop_keys})
        #jp.DoAction(action_id='set_filter',argument={'experiment_id':'profitLossLong-20190130-05a80d6a-2458-11e9-9bb0-062b1b6fe204','fields':['memory_use_mb','value_total','value_pl','current_date']})
        df = pd.DataFrame(jp.QueryData())
        return df

    def loadExperimentManagerData(self,keys = ['experiment_id','last_contacted','name','status']):
   #
        # Official Experiment Manager process properties
        
        #df = em.listexpts(status=['running'])     
        dfs = []
        experimentType =  self.get_filter_value('etype')

        # Running
        # -------
        df = self.em.listexpts(status=['running'])
        for k in keys:
            if k not in df.columns:
                df[k] = ""
        df = df[keys]
        dfs.append(df)
        
        # Failing
        # -------
        df = self.em.listexpts(query={'auto_restart':True, 
                                 'status':{'$in':['cleared','crashed','halted','killed','completed']}})
        
        for k in keys:
            if k not in df.columns:
                df[k] = ""
        if len(list(df.index)) > 0:
            df['last_contacted'] = "null"
            df['auto_restart'] = True
            df = df[keys]
            dfs.append(df)

        # Queued
        # -------
        df = self.em.listqueue()
        for k in keys:
            if k not in df.columns:
                df[k] = ""
        if len(list(df.index)) > 0:
            df['status'] = "queued"
            df['last_contacted'] = "null"
            df = df[keys]
            dfs.append(df)
        
        #df = self.em.listexpts(status=['completed'])     
        #df = df[keys]
        #dfs.append(df)
        #df = self.em.listexpts(status=['killed'])     
        #df = df[keys]
        #dfs.append(df)
        #df = self.em.listexpts(status=['crashed'])
        #df = df[keys]
        #dfs.append(df)


        #df = self.em.listqueue()
        #df['status'] = "queued"
        #df['last_contacted'] = "null"
        #df = df[keys]
        #dfs.append(df)
        
        
        df = pd.concat(dfs)#,sort=True)
        return df

    def load_data_buffer(self):
        self.exp_conn = {'mongo_server':conf.get( "jef_mongo_host", "54.184.199.101" ) ,
                         'mongo_port':conf.get( "jef_mongo_port", 27017 ),
                         'mongo_username':conf.get( "jef_mongo_username", "pax_user" ),
                         'mongo_password':conf.get( "jef_mongo_password", "paxuser43" ),
                         'mongo_authSource':conf.get( "jef_mongo_authSource", "fleetRover" ),
                         'mongo_database':conf.get( "jef_mongo_object_database", "fleetRover" ),
                         'mongo_collection':conf.get( "jef_mongo_experiments_collection", "experiments" ) ,}        

        self.exp_prop = {'mongo_server':conf.get( "jef_mongo_host", "54.184.199.101" ) ,
                         'mongo_port':conf.get( "jef_mongo_port", 27017 ),
                         'mongo_username':conf.get( "jef_mongo_username", "pax_user" ),
                         'mongo_password':conf.get( "jef_mongo_password", "paxuser43" ),
                         'mongo_authSource':conf.get( "jef_mongo_authSource", "fleetRover" ),
                         'mongo_database':conf.get( "jef_mongo_object_database", "fleetRover" ),
                         'mongo_collection':conf.get( "jef_mongo_properties_collection", "properties" ) ,}        
        
        #
        # Properties saved by the algorithm itself
        prop_keys = ['memory_use_mb','value_total','value_pl','current_date','expmode','etype']
        df_prop = self.loadAdditionalData(prop_keys,self.exp_prop)

        #
        # Properties loosely refrences by the experiment manager
        exp_keys = ['auto_restart','trace_memory']
        df_exp = self.loadAdditionalData(exp_keys,self.exp_conn)

        core_keys = ['experiment_id','last_contacted','name','status']
        df_core = self.loadExperimentManagerData(core_keys )   
        
        dffinal = pd.merge(df_core, df_prop, how = 'left', left_on = 'experiment_id', right_on = 'experiment_id')
        dffinal = pd.merge(dffinal, df_exp, how = 'left', left_on = 'experiment_id', right_on = 'experiment_id')
        dffinal = dffinal.fillna(0)
        #dffinal .loc[dffinal ['etype'] == "",'etype'] = "algorithm"

        #
        ## First, create the data
        self.data = {
            }
        for k in (prop_keys + core_keys + exp_keys): 
            self.data [k] = list(dffinal[k])


class JefPropertiesReader(BufferedQueryInterface):
    def do_init(self):
        self.data = {
            'item':[],
            'key':[],
            }      
        self.registerId('experiment_id','each entry has a unique experiment id')
        self.registerFilter(filter_id='fields',default=None,description="The fields you want queried, try ['memory_use_mb','value_total','value_pl','current_date']")
        self.registerFilter(filter_id='experiment_id',default=None,description="Search, and show, only the data for one experiment (saves db use)")

        self.exp_conn =self._settings['connection']
        
    
    def load_data_buffer(self):
        fields =  self.get_filter_value('fields')
        eid =  self.get_filter_value('experiment_id')
        if not fields:
            return
        self.data ={}
        self.data ['experiment_id'] =  []
        for f in fields:
            self.data [f] =  []


        self.obc = objectConf(self.exp_conn)
        if eid:
            self.obc.setKey({'experiment_id':eid})
            self.obc.load()
            props = self.obc.getSettings()
            self.loadProps(props)
        else:
            propList = self.obc.find({'experiment_id':{ '$exists' : True } })
            for props in propList:
                self.loadProps(props)

    def loadProps(self,props):
        for key in self.data.keys():
            if key in props:
                self.data [key].append(props[key])
            else:
                self.data [key].append(None)

class JefSystemOut(BufferedQueryInterface):

    def do_init(self):
        self.data = {
            'date':[],
            'system_out':[],
            }      
        self.registerId('date','each log entry has a unique date')
        self.registerFilter(filter_id='experiment_id',default=None,description="The field that uniquely describes an experiment")
        self.em = self._settings['market_data'].getEm()

                    
    def load_data_buffer(self):
        eid =  self.get_filter_value('experiment_id')
        if not eid :
            return
        dataIn = self.em.get_data(experiment_id=eid)
        
        if 'stdout' in dataIn  and 'stderr' in dataIn and 'date' in dataIn:
            std = []
            for index, row in dataIn.iterrows():
                string = ""
                string  = string + str(row['stderr'])
                string  = string + str(row['stdout'])
                std.append(string)

            self.data ['system_out'] = std
            self.data ['date'] =  list(dataIn['date'])
        elif 'stderr' in dataIn and 'date' in dataIn:
            display(dataIn['stderr'])
            self.data ['system_out'] =  list(dataIn['stderr'])

        elif 'stdout' in dataIn and 'date' in dataIn:
            display(dataIn['stdout'])
            self.data ['system_out'] =  list(dataIn['stdout'])
            self.data ['date'] =  list(dataIn['date'])
        else:
            print("Warning -- partial log data found for experiment ",str(eid ), " 265 of DataQueries.py")



class JefFileText(BufferedQueryInterface):

    def do_init(self):
        self.data = {
            'file':[],
            'filename':[]
            }      
        self.registerId('filename','each log entry has a unique date')
        self.registerFilter(filter_id='experiment_id',default=None,description="The field that uniquely describes an experiment")
        self.em = self._settings['market_data'].getEm()

                    
    def load_data_buffer(self):
        eid =  self.get_filter_value('experiment_id')
        if not eid :
            return

        gb=self.em.get_ipynb(experiment_id=eid)
        if not gb:
            gb=self.em.get_py(experiment_id=eid)

        self.data['file'].append( gb)
        self.data['filename'].append('experiment.ipynb')

class AutotradePerformanceTimeseries(BufferedQueryInterface):
    '''
        This class gives the user various methods that 
        pull data from financial processes

        TODO Generalize so this class supports both

    '''
    def do_init(self):
        if 'mode' not in self._settings:
            self._settings['mode'] = 'backtest'

        self.data = {
        'pl_value':[],
        'value':[],
        'date':[],
        }
        self.registerId('date',"each timeseries event is uniquely identified by its date")
        self.registerFilter(filter_id= 'experiment_id',default = None, description ="the timeseries analysis is always shown for a valid experiment id")
        self.cost_base =  0.001
        self.client = pymongo.MongoClient( host = conf.get( "advice_mongo_host", "54.184.199.101" ), 
                                   port = conf.get( "advice_mongo_port", 27017 ),
                                   username = conf.get( "advice_mongo_username", "pax_user" ),
                                   password = conf.get( "advice_mongo_password", "paxuser43" ),
                                   authSource = conf.get( "advice_mongo_authSource", "fleetRover" ) )        
        self.em = self._settings['market_data'].getEm()
        self.backtest_date = datetime.datetime(2019,1,1)

    def getAutotrades(self):
        eid = self.get_filter_value('experiment_id')
        assert eid

        cur = self.client.advice.autotrades.find({'experiment_id':eid}).sort([('purchase_date',pymongo.ASCENDING)])
        autotrades = []
        for row in cur:
            autotrades.append(row)
        return autotrades 
    
    def load_data_buffer(self):
        eid = self.get_filter_value('experiment_id')
        if not eid:
            return
        try:
            # Query 
            dataIn = self.em.get_data(experiment_id=eid)
            if dataIn.empty or 'current_date' not in list(dataIn.columns):
                self.data = {
                'pl_value':[],
                'value':[],
                'date':[],
                }
                return
            dataIn = dataIn[dataIn['current_date'].notnull()]
            if self._settings['mode'] == 'backtest':
                dataBT = dataIn[dataIn['current_date'] < self.backtest_date]
            else:
                dataBT = dataIn[dataIn['current_date'] > self.backtest_date]
        except   Exception as e:
            import traceback
            traceback.print_exc()
            print (str(e))
            display(pd.DataFrame(dataIn))
            raise e
        #### Every individual trade
        #
        # completeTradeList = []
        # for tradeList in dataBT['settled_autotrades']:
        #    for trade in tradeList:
        #        completeTradeList.append(trade)
        # completeTradeList = pd.DataFrame(completeTradeList)
        #  The performance data, and performance metrics
        ##for k in list(completeTradeList.columns):
        ##    self.data[k] = list(completeTradeList[k])
        
        self.data = {
            'pl_value':list(dataBT['value_pl_holding']),
            'value':list(dataBT['value_total']),
            'date':list(dataBT['current_date']),
            }
    #def do_refresh(self):
    #    self._settings['refresh'] = True
    #    self.load_data_buffer()
    #    self.dataNotify()
        #
        ## Second, register the append action so it can be used.
        
    #def setExperiment(self,indicesIn= None,argumentIn=None):
    #    self._settings['experiment_id'] = argumentIn['experiment_id']
    #    self._settings['cost_base'] = 0.001
    #    self.do_refresh()
       
        #self.registerAction('halt',AlgorithmQuery.deleteAction)


class AutotradesQuery(BufferedQueryInterface):
    '''
        This class gives the user various methods that 
        pull data from financial processes

        TODO Generalize so this class supports both

    '''
    def do_init(self):
        if 'mode' not in self._settings:
            self._settings['mode'] = 'backtest'

        self.data ={
             'amount': ["Early fail"],'bottom_sell': [],'close_date': [],'command_sell': [],'experiment_id': [],
             'final_price': [],'high_sell': [],'last_price': [],'order_id': [],'pl': [],
             'purchase_date': [],'security': [],'sell_event': [],'time_sell': []}

        self.registerId('date',"each timeseries event is uniquely identified by its date")
        self.registerFilter(filter_id= 'experiment_id',default = None, description ="the timeseries analysis is always shown for a valid experiment id")
        self.registerFilter(filter_id= 'date_start',default = None, description ="the date to limit the query to")
        self.registerFilter(filter_id= 'date_end',default = None, description ="the date to limit the query to")

        self.client = pymongo.MongoClient( host = conf.get( "advice_mongo_host", "54.184.199.101" ), 
                                   port = conf.get( "advice_mongo_port", 27017 ),
                                   username = conf.get( "advice_mongo_username", "pax_user" ),
                                   password = conf.get( "advice_mongo_password", "paxuser43" ),
                                   authSource = conf.get( "advice_mongo_authSource", "fleetRover" ) )        
        self.em = self._settings['market_data'].getEm()
        self.error = ""

    def load_data_buffer(self):
        print("LOADING")
        eid = self.get_filter_value('experiment_id')
        date_start = self.get_filter_value('date_start')
        date_end = self.get_filter_value('date_end')
        dn = datetime.datetime.now()

        if not date_start:
            date_start = datetime.datetime(dn.year,dn.month,dn.day,0,0,0)
        if not date_end:
            date_end = datetime.datetime(dn.year,dn.month,dn.day,23,0,0)
        delta = date_end - date_start
        days = delta.days
        if not eid:
            return
        try:
            # Query 
            dataIn = self.em.get_data(experiment_id=eid)
            dataIn = dataIn[dataIn['current_date'].notnull()]
            dataIn = dataIn[dataIn['current_date'] < date_end]
            dataIn = dataIn[dataIn['current_date'] > date_start]

        except   Exception as e:
            import traceback
            traceback.print_exc()
            self.error = str(e) 
            print (str(e))
            display(pd.DataFrame(dataIn))
            raise e

        #### Every individual trade
        completeTradeList = []
        ordersAdded = []
        for tradeList in dataIn['settled_autotrades']:
            for trade in tradeList:
                print(trade)
                completeTradeList.append(trade)
                ordersAdded.append(trade['order_id'])

        for tradeList in dataIn['new_autotrades']:
            for trade in tradeList:
                if trade['order_id'] not in ordersAdded:
                    print(trade)
                    completeTradeList.append(trade)
                    ordersAdded.append(trade['order_id'])
        completeTradeList = pd.DataFrame(completeTradeList)
        if len(list(completeTradeList.index))==0:
            self.data ={
                 'amount': [],'bottom_sell': [],'close_date': [],'command_sell': [],'experiment_id': [],
                 'final_price': [],'high_sell': [],'last_price': [],'order_id': [],'pl': [],
                 'purchase_date': [],'security': [],'sell_event': [],'time_sell': []}
        else:
            length = len(list(completeTradeList.index))
            cols  =list(completeTradeList.columns)
            for k in  self.data.keys():
                #self.data[k] =completeTradeList[k]
                if k in cols:
                    self.data[k] =completeTradeList[k]
                else:
                    self.data[k] = [None for i in range(0,length)]

class OrderQuery(BufferedQueryInterface):

    def do_init(self):
        self.me = self._settings['market_data'].getMe()
        self.data = {
            'experiment_id':[],
            'purchase_date':[],
            'security':[],
            'cost':[],
            'order_id':[],
            'time_sell':[],
            'high_sell':[],
            'bottom_sell':[],
            'pl':[],
            
            }       
        self.registerAction('addOrder' ,OrderQuery.addOrder, "Add an order into the simulation", "None")
        self.registerAction('closeOrder' ,OrderQuery.closeOrder, "Close out the position of an order",['TYPE_INDICES'])
        self.registerId('order_id',"The id of an order than can uniquely identify any bracket order")
        #raise Exception("Implement this")
    '''
        Get realtime stock data, and handle orders
    '''

    def load_data_buffer(self):

        try: 
            self.data = {
                'experiment_id':[],
                'purchase_date':[],
                'security':[],
                'cost':[],
                'order_id':[],
                'time_sell':[],
                'high_sell':[],
                'bottom_sell':[],
                'pl':[],
                
                }       
            #print('trades',str(len(self.me.context['autotrades'])))
            
            for trade in self.me.context['autotrades']:
                for key in trade:
                    if key in self.data:
                        self.data[key].append(trade[key])
                self.data['pl'].append(self.me.context['current_price'][trade['security']]['Open'] / trade['last_price'])
            #print(self.data)
            
            if 'value_div' in self._settings:
                string = "Account Value: " + str(self.me.context['value_total']) + "<br>"
                string = string + "Holding Value: " + str(self.me.context['value_holding']) + "<br>"
                string = string + "Holding Value: " + str(self.me.context['value_cash']) + "<br>"
                self._settings['value_div'].div.text = string
        except   Exception as e:
            import traceback
            traceback.print_exc()
            print (str(e))            
          
        #
        ## Second, register the append action so it can be used.
        
    def addOrder(self,indicesIn= None,argumentIn=None):
        self.me.do_order_bracket(k='AAPL',
                                  testOrder=False,
                                  limit_timedelta=datetime.timedelta(days=1),
                                 limit_min=0,
                                 limit_max=1000)
        self.refresh()
    
    def closeOrder(self,indicesIn=None,argumentIn=None):
        print("closing indicesIn ",indicesIn)
        print("closing argumentIn ",argumentIn)
        if indicesIn:
            for i in indicesIn:
                print("closing ",self.data['order_id'][i])
                self.me.do_close_bracket(self.data['order_id'][i])




class RealtimePaperTrader(BufferedQueryInterface):
    '''
        Get realtime stock data, and handle orders
    '''

    def do_init(self):
        self.me = self._settings['market_data'].getMe()
        for i in range(0,10):
            self.me.run_step()

        self.data = {
            'stream_symbol':[],
            'stream_open':[],
            'stream_close':[],
            'stream_date':[],
            }
        #self.client = pymongo.MongoClient( host = conf.get( "advice_mongo_host", "54.184.199.101" ), 
        #                           port = conf.get( "advice_mongo_port", 27017 ),
        #                           username = conf.get( "advice_mongo_username", "pax_user" ),
        #                           password = conf.get( "advice_mongo_password", "paxuser43" ),
        #                           authSource = conf.get( "advice_mongo_authSource", "fleetRover" ) )        
        

        self.registerAction('closeOrder' ,OrderQuery.closeOrder, "Close out the position of an order",self.Parameter.INDICES)
        self.registerId('date',"The instant of any time series event")
        self.registerFilter('symbol',"AAPL","The stock symbol all of this data is about")

    
    def update_data_buffer(self):  
        self.me.run_step()   
        secsymbol = self.get_filter_value('symbol')
        if 'current_price' in self.me.context and secsymbol in self.me.context['current_price']:
            openPrice = self.me.context['current_price'][secsymbol]['Open']
            closePrice = self.me.context['current_price'][secsymbol]['Close']
            self.data['stream_open'].append(openPrice)
            self.data['stream_close'].append(closePrice)
            self.data['stream_date'].append(self.me.context['current_date'])
            self.data['stream_symbol'].append(secsymbol)
            ## Append data
            while len(self.data[list(self.data.keys())[0]]) > 100:
                self.data['stream_symbol'].pop(0)
                self.data['stream_open'].pop(0)
                self.data['stream_close'].pop(0)
                self.data['stream_date'].pop(0)
            pass

    def load_data_buffer(self):
        pass
        #dataIn = em.get_data(experiment_id=self._settings['symbol'])        



class ClientQuery(BufferedQueryInterface):
    def do_init(self):
        self.data = {
        'active':[],
        'date':[],
        'name':[],
        'email':[],
        'secs':[],
        'served':[],
        'test':[],
        'user_id':[],
        'welcome_email':[],
        }
        self.registerId('email',"each user is uniquely identified by their email")
        client = pymongo.MongoClient( host = conf.get( "advice_mongo_host", "54.184.199.101" ), 
                                   port = conf.get( "advice_mongo_port", 27017 ),
                                   username = conf.get( "advice_mongo_username", "pax_user" ),
                                   password = conf.get( "advice_mongo_password", "paxuser43" ),
                                   authSource = conf.get( "advice_mongo_authSource", "fleetRover" ) )        
        db = client.advice
        self.users = db.users
        self.pool = db.pool
        self.registerAction('sent_welcome',ClientQuery.sentWelcome)

    def sentWelcome(self,indicesIn=None,argumentIn=None):
        if indicesIn:
            for i in indicesIn:
                user_id = self.data['user_id'][i]
                result = self.users.find_one_and_update( filter = {'user_id':user_id },
                                                             update = {'$set':{'welcome_email':True}})

    def getUsers(self):
        curuser = self.users.find()
        curpool = self.pool.find()
        userdata = {}
        pooldata = {}
        for row in curpool:
            try:
                user_id = row['user_id']
                pooldata [user_id] = row
            except:
                pass
        for row in curuser:
            try:
                user_id = row['user_id']
                userdata[user_id] = row
                userdata[user_id].update(pooldata [user_id])
            except:
                pass
        return userdata
    
    def load_data_buffer(self):
        data = self.getUsers()
        #import pprint
        #pprint.pprint(data)
        df = pd.DataFrame(data) 
        df = df.transpose()
        for k in self.data.keys():
            if k in list(df.columns):
                self.data[k] = list(df[k])      


import requests
import datetime
import json
class api:
    def __init__(self,key,server_address="http://dev.paxculturastudios.com:5000"):
        self.key = key 
        self.server_address = server_address 
        
    def poll_stream(self,stream_id='/api/autotrade/get/', date_start=None,date_end=None):
        if date_start == None:
            date_start = datetime.datetime.now()
        if date_end == None:
            date_end = datetime.datetime.now() - datetime.timedelta(days=3)
        
        assert isinstance(stream_id,str)
        assert isinstance(date_start,datetime.datetime)
        assert isinstance(date_end,datetime.datetime)
        payload = {'apikey': self.key}
        r=requests.get(
            self.server_address+stream_id ,
            data=payload,
            params = payload
            )
        return json.loads(r.text)

#Force a query through the API Engine

class AutotradeAPIQuery(BufferedQueryInterface):
    def do_init(self):
        self.data = {
            'security':[],
            'purchase_date':[],
            'bottom_sell':[],
            'high_sell':[],
            'last_price':[],
            'final_price':[],
            'close_date':[],
            'pl':[],
            'apikey':[]
        }
        self.registerId('apikey',"an api key is required to refresh data")
        self.registerFilter('apikey',"an api key is required to refresh data")
        self.registerFilter(filter_id='apikey',default=None,description="an api key is required to refresh data")


    def getData(self):
        a = api(key="justin1337",server_address=conf.get('autotrade_server',"http://dev.paxculturastudios.com:5000"))
        t = a.poll_stream("/api/autotrade/get/")
        return t

    def load_data_buffer(self):
        apikey =  self.get_filter_value('apikey')
        if apikey == None:
            return 
        import pprint
        data = self.getData()
        df = pd.DataFrame(data) 
        length = len(list(df.index))
        for k in self.data.keys():
            if k in list(df.columns):
                self.data[k] = list(df[k])
            else:
                self.data[k] = [apikey for i in range(0,length)]
    

    
class SendWelcomeEmail(ActionButton):
    @staticmethod
    def emailBody(user_id=None):
        user_id_str = "Please email admin@paxculturastudios.com for you private API key. We will have a few questions about how you will be using the API"
        if user_id:
            user_id_str = "Your API Key is "+user_id

        emailBodyText = """
        <h1>Welcome to the trial!</h1>
        <b>"""+user_id_str+"""</b>
        <br>
        <h2>Today we predict the stock market</h2>
        <p>Imagine you had a team of robots watching and analyzing each security you cared about. </p>
        <br>
        <h2>How does it work</h2>
        <ul>
        <li>1. Save your API Key</li>
        <li>(or) 3. Access your API in python (see www.paxculturastudios.com) </li>
        <li>4. Start saving your free data, and see the results for yourself</li>
        </ul>

        <p> This information generates profit. When you reach the point where you (a) want to manage your own algorithms, or (b) need a real-time data stream for your team, drop us a line.</p>
        <p>for now, during the trial, you are invited to email justingirard@paxculturastudios.com .</p>
        """
        return emailBodyText


    def handle_selection(self,event,ids,idfields):
        for emailAddress in ids:
            try:
                resp = self.send_simple_message(client_email = emailAddress,email_body=SendWelcomeEmail.emailBody())
                if resp.status_code == 200:
                    print("it sent!")
                    super().handle_selection(event,ids,idfields)
                    print ("SENT! ",emailAddress)
                else:
                    print("Did not send!")
            except Exception as e:
                print(e)

    def handle_no_selection(self,event):
        #print(self._settings)
        pass
    def send_simple_message(self, client_email="justingirard@justingirard.com", email_body = ''):
        server_id = conf.get("server_id"," [DEVELOPMENT]")
        paxlogo_file = conf.get('paxlogo_file','/home/ec2-user/signals/app/paxlogo.jpg')
        subject_line =  "Welcome to the Pax Financial Alpha Test"
        print({"from": "Pax Financial <justingirard@paxculturastudios.com>",
                  "to": [client_email],
                  "subject": subject_line,
                  "html": email_body  # compose email
                  })
        r=requests.post(
            "https://api.mailgun.net/v3/mg.paxculturastudios.com/messages",
            auth=("api", "f27f39814bf328af7c39321d550c46dc-4836d8f5-98f0e3ba"),
            #files=file_list,
            data={"from": "Pax Financial <justingirard@paxculturastudios.com>",
                  "to": [client_email],
                  "subject": subject_line,
                  "html": email_body  # compose email
                  }
            )
        return r
