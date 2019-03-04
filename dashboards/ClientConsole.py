

import sys
sys.path.append('../../')

import datetime
import pandas_datareader as pdr

from bokehComponents.Dashboard import Dashboard
from bokehComponents.BokehComponents import BufferedQueryInterface,QueryTableComponent,InteractiveDataGroup,LoadButton
from bokehComponents.BokehComponents import ActionButton,BokehTimeseriesGraphic,BokehButton,ExperimentTable
from jad.dashboards.DataQueries import ClientQuery


from bokeh.io import output_notebook,output_file
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models.widgets import Panel, Tabs #, DataTable, DateFormatter, TableColumn, Tabs, 
from bokeh.layouts import layout
from bokeh.plotting import figure,show,output_file
from bokeh.models import Div
from conf.conf import conf
from conf.conf import objectConf
import requests

class SendWelcomeEmail(ActionButton):
    emailBody = """
    <h1>Welcome to the trial!</h1>
    <p>Over the last 7 years, Justin Girard and the Pax team have been doing what is called 'online timeseries regression'. In fact, in 2012, Justin Girard, discovered and published 
    landmark work in the field of 'concurrent markov decision processes'. What this means, to most people, is that Justin discovered a way to make an uncountable amount of robots study 
    streaming data together.</p>
    <br>
    <h2>Today we predict the stock market</h2>
    <p>Imagine you had a team of robots watching and analyzing each security you cared about. In 2016, after consulting for only a few years, Justin retired and founded Pax Financial, and FleetOps. Today he is
    granting access to one of the streaming algorithms he used to predict the market. Today, Justin advises the Pax Financial team and the FleetOps team.</p>
    <br>
    <h2>How does it work</h2>
    <ul>
    <li>1. Save your API Key</li>
    <li>2. Download the user plugin for Chrome</li>
    <li>(or) 3. Access your API in python</li>
    <li>4. Start saving your free data, and see the results for yourself</li>
    </ul>

    <p> This information generates profit. When you reach the point where you (a) want to manage your own algorithms, or (b) need a real-time data stream for your team, drop us a line.</p>
    <p>for now, during the trial, you are invited to email justingirard@paxculturastudios.com .</p>
    """


    def handle_selection(self,event,ids,idfields):
        for emailAddress in ids:
            try:
                resp = self.send_simple_message(client_email = emailAddress,email_body=SendWelcomeEmail.emailBody)
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


class ClientConsole(Dashboard):    
    
    
    def getControlArea(self):
        
        ###############################
        #
        # Top Pane
        #
        
        visuals = []
        button_defs = [{'label':'Send Welcome','action':'sent_welcome','class':SendWelcomeEmail,'datasource_id':'clients','selection':True}]
        datasources = []
        
        datasources.append({'class':ClientQuery,
                        'datasource_id':'clients'})
        visuals.append({'class':ExperimentTable,
                        'width':800,
                        'height':300,
                        'date_keys':['date'],
                        'title':"Client List",
                        'hide':[],
                        #'q_key':'status',
                        #'q_value':'running',
                        #'q_operator':'=',
                        'datasource_id':'clients'
                       })

        
        self.dw = InteractiveDataGroup({'datasources':datasources,
                        'visuals':visuals,
                        'commands':button_defs,
                        })    
        layoutList = []
        layoutList.append(self.getConsole([self.dw]))
        
        
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
