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

from p2ner.abstract.interface import Interface
from twisted.internet import reactor
from p2ner.core.components import getComponents as getComp
from p2ner.core.components import getComponentsInterfaces as getCompInt
from p2ner.base.Stream import Stream
from p2ner.util.interfacelog import DatabaseLog
from twisted.internet.threads import deferToThread


class localControl(Interface):
    
    def initInterface(self):
        self.logger=DatabaseLog(_parent=self)
        
    def start(self):
        pass
        
        
    def cleanUp(self):
        pass
        
    def registerStream(self,stream,input=None,output=None):
        strm=Stream(**stream)
        self.root.registerStream(strm,input,output)        
    
    def contactServers(self,server):
        for s in server:
            self.root.contactServers(s)
    
    def startProducing(self,id,type):
        self.root.startProducing(id)
    
    def startRemoteProducer(self,id,type):
        self.root.startRemoteProducer(id)
        
    
    def subscribeStream(self,id,ip,port,output=None):
        self.root.subscribeStream(id,ip,port,output)

    
    def stopProducing(self,id,changeRepub=False):
        self.root.stopProducing(id,changeRepub)
    
    def unregisterStream(self,id):
        self.root.unregisterStream(id)
    
    def returnSubStream(self,stream,id):
        if stream==-1:
            self.log.info('could not subscribe stream with id %d',id)
        self.controlUI.succesfulSubscription(stream,id)
        

    def returnStopProducing(self,id):
        self.controlUI.stopProducing(id)
            
    def returnUnregisterStream(self,id):
        self.controlUI.unregisterStream(id)
            
    def returnProducedStream(self,stream,hash=None):
        if stream==-1:
            self.log.info('could not register stream')
        self.controlUI.registerStream([stream])
           
    def returnContents(self,stream,server):
        if stream==-1:
            message= 'server is unreachable: %s : %s '%(server[0],server[1])
            self.log.info(message)
        self.controlUI.getStream(stream,server)

    def setLiveProducer(self,id,live):
        self.controlUI.setLiveProducer(id,live)
        
    def setLiveStream(self,id,live):
        self.controlUI.setLiveStream(id,live)
           
    def removeProducer(self,id):
        self.controlUI.stopProducing(id)
        
    def logRecord(self,record):
        if record.levelno==15:
            self.controlUI.newMessage(record.getMessage(),record.levelno)
            return
        elif record.name=='p2ner.network':
            self.controlUI.logNGui(record.getMessage())
        self.logger.addRecord(record)
        
    def getLogRecords(self,func):
        d=self.logger.getRecords()
        d.addCallback(func)
    
    def exiting(self):
        self.root.exiting()
        
    def displayError(self,error,quit=False):
        self.controlUI.displayError(error,quit)
    
        
    def getComponentsInterfaces(self,comp):
        c=getCompInt(comp)
        self.controlUI.preferences.setComponent(comp,c)
        
    def startConverting(self,gui,dir,filename,videorate,subs,subsFile,subsEnc):
        id=self.root.startConverting(dir,filename,videorate,subs,subsFile,subsEnc)
        gui.getConverterId(id)
   

    def getConverterStatus(self,gui,id):
        status=self.root.converters[id].getStatus()
        gui.setStatus(status)

    def abortConverter(self,id):
        converter=self.root.converters.pop(id)
        converter.abort()
        
    def getStatistics(self):
        return self.stats.keys()
    
    def getStatValues(self,stats):
        ret=[]
        for s,c in stats:
            count=self.stats[s]['count']
            if count>100:
                c=100 -( count - c)
            v=self.stats[s]['values'][c:]
            
            ret.append((s,v,count))
        return ret
    
    def networkUnreachable(self,status):
        reactor.callLater(0,self.displayError,'network conditions are not valid',True)
        self.networkStatus(status)
        
        
    def networkStatus(self,status):
        if status:
            self.controlUI.networkStatus(status,self.netChecker.externalIp,self.netChecker.measureBW)
            msg='network ok'
        else:
            self.controlUI.networkStatus(status,None,None)
            msg='network condintions are not valid'
        reactor.callLater(0.2,self.log.log,15,msg)
        
    def checkNetwork(self):
        reactor.callLater(0.2,self.log.log,15,'checking network conditions. Please wait...')
        reactor.callLater(0.3,self.netChecker.check)
        return
        
    def newChatMessage(self,id,message,peer):
        self.controlUI.chatClientUI.newChatMessage(id,message,peer)
        
    def newChatter(self,id,username,new):
        self.controlUI.chatClientUI.newChatter(id,username,new)
        
    def sendChatMessage(self,id,message,peer):
        self.chatClient.sendChatMessage(id,message,peer)
        
    def joinChatRoom(self,id,username,server):
        self.chatClient.joinChatRoom(id,username,server)
    
    def leaveChatRoom(self,id,username,server):
        self.chatClient.leaveChatRoom(id,username,server)

            
    def startBWMeasurement(self,ip,gui):
        self.root.startBWMeasurement(ip,gui)
        
    def setBW(self,bw):
        self.root.setBW(bw)
 
