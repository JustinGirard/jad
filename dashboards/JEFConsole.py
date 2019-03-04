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

class JobStarterQuery(BufferedQueryInterface):

    def getJobStarterStatus(self):

        import socket; 
        myip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        import sys
        import pandas as pd
        from pymongo import MongoClient
        sys.path.append('../../')
        from conf.conf import objectConf
        from conf.conf import conf

        host = conf.get( "jef_mongo_host", "54.184.199.101" ) 
        port = conf.get( "jef_mongo_port", 27017 )
        username = conf.get( "jef_mongo_username", "pax_user" )
        password = conf.get( "jef_mongo_password", "paxuser43" )
        authSource = conf.get( "jef_mongo_authSource", "fleetRover" )
        obj_database = conf.get( "jef_mongo_object_database", "fleetRover" )
        obj_collection = conf.get( "jef_mongo_jobstarter_collection", "jobstarter_properties" )
        conn = {'mongo_server':host,
                               'mongo_port':port,
                               'mongo_username':username,
                               'mongo_password':password,
                               'mongo_authSource':authSource,
                               'mongo_database':obj_database,
                               'mongo_collection':obj_collection,}



        op = objectConf(conn)
        rec = op.find({'log_type':'job_starter'})
        status = []
        for r in rec:
            x = r
            x['_id'] = str(x['_id'])
            if 'identity' in r:
                for k in r['identity'].keys():
                    x[k] = r['identity'][k]
            status.append(x)
        return status

    def do_init(self):
        self.registerId('instanceId','The aws id of the instance to be managed and observed')
        self.registerFilter('instanceId',None,'The aws id to filter the list by')

        pass

    def load_data_buffer(self):
        # return if it's not time to refresh, or if this has never run.
        jss = self.getJobStarterStatus()
        inst_list = self.getAwsInstances()
        leftList = inst_list.copy()
        self.invincible_list = ["i-05e75507bcaf12912","i-0f912f5debf39abd3"]
        
        #
        # Label and pre precess jobStarters
        for js in jss:
            for instanceId in inst_list:
                if instanceId == js['instanceId']:
                    leftList.remove(instanceId)
            js['spot']= True
            if js['instanceId'] in self.invincible_list:
                js['spot']= False
        #
        # Add all instances to list
        for l in leftList:
            jss.append({ 
            'spot': "Unknown",
            'last_run': datetime.datetime(2010,1,1),
            'name': "Unknown",
            'privateIp': "Unknown",
            'instanceId': str(l),
            'memoryAverage': "Unknown",
            'log_type': "Unknown",   
            'imageId':"Unknown",
            'print':"Unknown"
            })
        
        #
        # Remove stopped servers
        for i in reversed(range(0,len(jss))):
            if jss[i]['instanceId'] not in inst_list:
                jss.pop(i)
        
        df = pd.DataFrame(jss)    
        '''
        _id, accountId, architecture, availabilityZone, billingProducts, devpayProductCodes,
        identity, imageId, instanceId, instanceType, kernelId, last_run, loadAverage,
        log_type, marketplaceProductCodes, memoryAverage, name, num_jobs_can_launch, pendingTime,
        print, privateIp, ramdiskId, region, self, version,
        '''
        self.data = { 
            'spot': [],
            'last_run': [],
            'name': [],
            'privateIp': [],
            'instanceId': [],
            'memoryAverage': [],
            'log_type': [],   
            'imageId':[],
            'print':[]
            }
        instanceIdList = list(df['instanceId'])
        all = True
        if self.get_filter_value('instanceId'):
            all = False
        print("filter", str(self.get_filter_value('instanceId')))

        for k in self.data.keys():
            columnList = list(df[k])
            for i in range(0,len(columnList)):
                if(all==True or instanceIdList[i] in self.get_filter_value('instanceId')):
                    self.data[k ].append(columnList[i])

        
        self.registerAction('startInstance',JobStarterQuery.startInstance)
        self.registerAction('deleteInstance',JobStarterQuery.deleteInstance)    
    
    def deleteInstance(self,indicesIn= None):
        import boto3
        ec2 = boto3.resource("ec2", region_name="us-west-2")
        if indicesIn:
            for iid in indicesIn:
                print( 'Delete Instance ' + str(self.data['instanceId'][iid]))
                if self.data['instanceId'][iid] in self.invincible_list:
                    return print("Aborting. Do not select system instances")
                if self.data['spot'][iid] != True:
                    return print("Aborting. Do not delete non-spot instances.")
                instance = ec2.Instance(self.data['instanceId'][iid])
                instance.terminate()
                print( 'TERMINATE SENT: ' + str(self.data['instanceId'][iid]))
                
    def startInstance(self,indicesIn= None):
        import boto3
        import datetime
        client = boto3.client('ec2')
        response = client.request_spot_instances(
            DryRun=False,
            SpotPrice='0.10',
            ClientToken='JEF_Process_3'+ str(datetime.datetime.now()),
            InstanceCount=1,
            Type='one-time',
            LaunchSpecification={
                'ImageId': 'ami-03901e3d5432761c6',
                'KeyName': 'default',
                'SecurityGroups': ['default'],
                'InstanceType': 't2.large',
                'Placement': {
                    'AvailabilityZone': 'us-west-2b',
                },
                #  'BlockDeviceMappings': [
                #    {
                #        'Ebs': {
                #            'SnapshotId': 'snap-09338fdae684dbc5c',
                #            'VolumeSize': 200,
                #            'DeleteOnTermination': False,
                #            'VolumeType': 'gp2',
                #            #'Encrypted': False
                #        },
                #        'DeviceName':'/dev/sda1',
                #    },
                #],

                'EbsOptimized': False,
                'Monitoring': {
                    'Enabled': True
                },
                'SecurityGroupIds': [
                    'sg-e4a8069f',
                ]
            }
        )
        print (response)
        print ("SUBMITTED REQUEST TO AWS. PLEASE WAIT 5 MINUTES")
    

    def getAwsInstances(self):
        inst = []
        import boto3
        ec2 = boto3.resource("ec2", region_name="us-west-2")
        filters = [
            {
                'Name': 'instance-state-name', 
                'Values': ['running']
            }
        ]

        # filter the instances based on filters() above
        instances = ec2.instances.filter(Filters=filters)
        for instance in instances:
            inst.append(str(instance.id))
        return inst


class JEFConsole(Dashboard):    
    
    def getControlArea(self):

        visuals = []
        visuals.append({'class':ExperimentTable,'width':800,'height':150,'date_keys':['last_run'],'title':"Server List",'hide':['print'],'datasource_id':'detail_source'})
        visuals.append({'class':BokehDiv,'width':800,'height':200,'title':"System Out",'datasource_id':'detail_source'})
        detailGroup = InteractiveDataGroup({'datasources':[{'class':JobStarterQuery,'id_field':'instanceId','datasource_id':'detail_source'}],
                'visuals':visuals,
                'commands':[],
                })    
        
        #
        # Server List
        #
        visuals = []
        button_defs = []
        visuals.append({'class':ExperimentTable,'width':900,'height':150,'date_keys':['last_run'], 'title':"Server List",'hide':['print','log_type'],'datasource_id':'joblist'})
        button_defs.append ({'class':ActionButton,'action':'startInstance','label':'Start New','datasource_id':'joblist'})
        button_defs.append ({'class':ActionButton,'action':'deleteInstance','label':'Delete','datasource_id':'joblist'})
        button_defs.append ({'class':LoadButton,'action':'set_filter','label':'Show Detail','datasource_id':'joblist'})
        dst = detailGroup.getDatasources()
        print(dst)
        dw = InteractiveDataGroup({'datasources':[{'class':JobStarterQuery,'id_field':'instanceId','datasource_id':'joblist'}],
                        'visuals':visuals,
                        'commands':button_defs,
                        'datasource_targets':dst,
                        })    
        
        return layout([self.getConsole([dw]),self.getConsole([detailGroup])], sizing_mode='fixed')

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
