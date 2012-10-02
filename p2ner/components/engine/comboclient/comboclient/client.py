# -*- coding: utf-8 -*-
from p2ner.abstract.engine import Engine
from twisted.internet import reactor
from p2ner.core.components import loadComponent
#from p2ner.base.messages.bootstrap import ClientStartedMessage
from messages.streammessage import  StreamIdMessage, ContentsMessage, SubscribeMessage
from messages.messageobjects import RequestStreamMessage,StreamMessage,CheckContentsMessage,ClientStartedMessage
from p2ner.base.Peer import Peer
from cPickle import dumps


defaultStream = ("StreamClient", [], {})

class Client(Engine):
    
    def initEngine(self, *args, **kwargs):
        self.log.info('initing client')
        self.enableTraffic()
        self.enableUI(**kwargs)
        self.messages = []
        self.sidListeners = []
        self.checkServers={}
        self.streamListeners=[]
        self.waitingReply=[]
        self.converters={}
        self.holePuncher=loadComponent('plugin','HolePuncher')(_parent=self)
        self.netChecker=loadComponent('plugin','NetworkChecker')(_parent=self)
        self.rProducerInf=loadComponent('plugin','RemoteProducerController')(_parent=self)
        self.chatClient=loadComponent('plugin','ChatClient')(_parent=self)
        reactor.callLater(0.2,self.interface.checkNetwork)
        

                
    def registerStream(self,stream,input,output):
        print output['comp']
        p=stream.getServer()
        server=Peer(p[0],p[1])
        server.dataPort=int(p[1])+1
        
        if self.netChecker.upnp: 
            port=self.netChecker.upnpDataPort
        else:
            port=self.netChecker.extDataPort
        
        p=None
        if self.netChecker.nat:
            p=Peer(self.netChecker.localIp,self.netChecker.controlPort,self.netChecker.dataPort)
        
        bw=int(self.trafficPipe.getElement("BandwidthElement").bw/1024)
        reactor.callLater(0.1, ClientStartedMessage.send, port,bw, p,server, self.controlPipe)
        self.log.debug('adding stream id message to listeners')
        m=StreamIdMessage(stream,input,output)
        self.sidListeners.append(m)
        self.log.debug('sending stream message to %s',server)
        reactor.callLater(0.5,StreamMessage.send,stream, server, self.controlPipe,m.checkResponse) 
        
   
    def newStream(self, stream,input,output):
        if self.getPStream(stream.id):
            self.log.error('stream with id %d already exists',stream.id)
            raise ValueError("Stream already exists")
        s, a, k = ('StreamProducer',[],{})
        
        self.log.debug('trying to load %s',s)
        streamComponent = loadComponent("stream", s)
        k['stream']=stream
        if input:
            k['input']=(input['component'],[],{'input':input})
        if output:
            k['output']=(output['comp'],[],{})#{'output':output['kwargs']})
        
        self.producingStreams.append(streamComponent( _parent=self,**k))
        

    def contactServers(self,server):
        server=Peer(server[0],server[1])
        if server in self.checkServers.keys():
            return
        
        
        """
        if self.netChecker.upnp:
            port=self.netChecker.upnpDataPort
        else:
            port=self.netChecker.extDataPort
      
        reactor.callLater(0.1, ClientStartedMessage.send, port, None,server, self.controlPipe)
        """
        
        m=ContentsMessage(server)    
        self.checkServers[server]=m
        
        self.log.debug('sending check contents message to %s',server)
        reactor.callLater(0.1, CheckContentsMessage.send,server,self.controlPipe,m.checkResponse)
        
    
    def startProducing(self,id):
        stream=self.getPStream(id)
        if stream:
            stream.start()
            self.log.info('started producing')
            
        #self.interface.returnStartProducing('produce')
       
            

                
    def subscribeStream(self,id,ip,port,output=None):        
        if id in self.waitingReply:
            return
        
        if self.getStream(id):
            self.log.error('stream with id %d already exists',id)
            #raise ValueError("Stream already exists")
            return
        
        self.waitingReply.append(id)
        server=Peer(ip,port)
        server.dataPort=int(port)+1
        self.log.debug('sending client started message to %s',server)
        if self.netChecker.upnp:
            port=self.netChecker.upnpDataPort
        else:
            port=self.netChecker.extDataPort
            
        p=None
        if self.netChecker.nat:
            p=Peer(self.netChecker.localIp,self.netChecker.controlPort,self.netChecker.dataPort)
        bw=int(self.trafficPipe.getElement("BandwidthElement").bw/1024)
        reactor.callLater(0.1, ClientStartedMessage.send, port,bw,p,server, self.controlPipe)
        self.log.debug('sending request stream message to %s',server)
        m=SubscribeMessage(id,output)
        self.streamListeners.append(m)
        reactor.callLater(0.5, RequestStreamMessage.send, id, server, self.controlPipe,m.checkResponse)
        
        
    def newSubStream(self, stream,id,output=None):
        self.waitingReply.remove(id)
        if stream!=-1:
            s, a, k = ('StreamClient',[],{})
            self.log.debug('trying to load %s',s)
            streamComponent = loadComponent("stream", s)
            k['stream']=stream
            if output:
                k['output']=(output['comp'],[],{'output':output['kwargs']})
        
            self.streams.append(streamComponent( _parent=self,**k))   
        self.interface.returnSubStream(stream,id)
            
    def start(self):
        pass
    
    def startRemoteProducer(self,id):
        stream=self.getStream(id)
        if not stream:
            return 
        stream.startRemoteProducer()
        return True
    
    
    def stopProducing(self,id,changeRepub=False):
        stream=self.getPStream(id)
        if not stream:
            self.log.error("stream with id:%d doesn't exist",id)
            #raise ValueError('there is not such stream %d',id)
            return
        
        if changeRepub:
            stream.stream.republish=False
            
        stream.stop()
        
        self.interface.returnStopProducing(id)

            
    def unregisterStream(self,id):
        stream=self.getStream(id)
        if not stream:
            self.log.error("stream with id:%d doesn't exist",id)
            #raise ValueError('there is not such stream %d',id)
            return

        stream.stop()
        
        self.interface.returnUnregisterStream(id)
        
    def exiting(self):
        for s in self.getAllStreams():
            s.stop()
        reactor.callLater(1,self.quit)
        
    def quiting(self):
        self.exiting()
        #reactor.stop()
        
    def startConverting(self,dir,filename,videorate,subs,subsFile,subsEnc):
        id=len(self.converters.keys())
        self.converters[id]=loadComponent('plugin','Converter')()
        self.converters[id].startConverting(dir,filename,videorate,subs,subsFile,subsEnc)
        return id
        
    def startBWMeasurement(self,ip,gui=None,defer=None):
        loadComponent('plugin','TCPBandwidthClient')(ip,gui,defer).start()
        
    def setBW(self,bw):
        self.trafficPipe.call('setBW',bw)

        
def startClient():
    from twisted.internet import reactor
    P2NER = Client(_parent=None,UI=('GtkGui',[],{}))

    reactor.run()   
    
def startDaemonClient():
    from twisted.internet import reactor
    P2NER = Client(_parent=None,interface=('XMLRPCControlUI',[],{}))
    reactor.run()   
    
    
if __name__ == "__main__":
    startClient()
