#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

OFF=0
ON=1
INPROGRESS=2
PAUSE=3

from p2ner.abstract.interface import Interface
from gtkgui.interface.xml.xmlinterface import Interface
from proxyinterface import ProxyInterface
from twisted.internet import reactor

class PClient(Interface):
    def initInterface(self,parent,peer):
        self.parent=parent
        self.peer=peer        
        self.output={}
        self.output['comp']='NullOutput'
        self.output['kwargs']=None
        if self.proxy:
            self.interface=ProxyInterface(self,_parent=self)
            self.interface.setProxy(self.proxy)
            self.interface.setForwardPeer(peer)
        else:
            self.interface=Interface(_parent=self)
            url="http://"+peer[0]+':'+str(peer[1])+"/XMLRPC"
            self.interface.setUrl(url)
        
    def sendStartProducing(self,id,type):
        self.interface.startProducing(id,type)
        
    def sendStopProducing(self,id):
        self.interface.stopProducing(id,False)
        
    def stopProducing(self,id):
        self.parent.setStatus(self.peer,OFF)
        self.parent.setId(self.peer,-1)
        self.parent.producerStopped(id)
        
        
    def sendSubsribe(self,id,ip,port,output):
        self.interface.subscribeStream(id,ip,port,output)
        
    def succesfulSubscription(self,stream,id):
        if stream==-1:
            self.parent.setStatus(self.peer,OFF)
            self.parent.setId(self.peer,-1)
        else:
            self.parent.setStatus(self.peer,ON)
            self.parent.setId(self.peer,id)
            
    def sendUnregisterStream(self,id):
        self.interface.unregisterStream(id)
        
    def unregisterStream(self,id):
        self.parent.setStatus(self.peer,OFF)
        self.parent.setId(self.peer,-1)
        
    def sendNewBW(self,bw):
        self.interface.setBW(bw)
        reactor.callLater(1,self.interface.getBW)
                
    def checkBW(self,bw):
        self.parent.setBW(self.peer,bw)
        
    def restartServer(self):
        self.interface.restartServer()
        
    def getOutput(self):
        return self.output
    
    def setOutput(self,output):
        if "Vlc" in output:
            self.output['comp']='PureVlcOutput'
        elif 'Null' in output:
            self.output['comp']='NullOutput'
        elif 'Flv' in output:
            self.output['comp']='FlvOutput'
        
    def getNeighbours(self,id,ip,port,func):
        self.interface.getNeighbours(id,ip,port,func)
        
    def getLog(self,func,ip,port):
        self.interface.getVizirLogRecords(func,ip,port)
        
    def stopSwapping(self,stop,id):
        self.interface.stopSwapping(stop,id)
