# -*- coding: utf-8 -*
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


from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
from p2ner.core.components import loadComponent,getComponents
from p2ner.core.pipeline import Pipeline
import sys
from random import uniform
from p2ner.util.utilities import findNextConsecutivePorts
from p2ner.core.preferences import Preferences

defaultControl = ("UDPCM", [], {})
defaultTraffic = ("UDPDB", [], {})
defaultTrafficPipe = ("BlockPipe", [], {})
defaultControlPipe = ("MsgPipe", [], {})
defaultInterface= ('LocalControl',[],{}) #('XMLRPCControlUI',[],{}) #
defaultLogger=('Logger',{})


class Engine(Namespace):

    def sanityCheck(self, requirements):
        return
        for var in requirements:
            if var not in self.g:
                raise ValueError("%s is not a valid variable in current environment" % var)

    @initNS
    def __init__(self, *args, **kwargs):
        
        self.useHolePunching=False
        self.streams = []
        self.producingStreams = []
        self.__stats__ = []
        
        ##INTERFACE
        interface=defaultInterface
        if "interface" in kwargs:
            interface=kwargs['interface']
            
        c, a, k = interface
        print c
        interface = loadComponent('interface', c)
        self.interface = interface(_parent=self, *a, **k)
        self.interface.start()

        ##LOGGER
        if 'logger' not in kwargs:
            logger=defaultLogger
        else:
            logger=kwargs['logger']
        c,k=logger
        self.logger=loadComponent('plugin',c)(**k)
        self.log=self.logger.getLoggerChild('base',interface=self.interface)

        ##Preferences
        self.preferences=Preferences(_parent=self)
        self.preferences.start()
        
        ##TEMPORARY LOAD STATS
        stats=self.preferences.getActiveStats()
        for s in stats:
            self.__stats__.append(loadComponent("stats", s[0])(_parent=self,**s[1]))
        
        if 'stats' in kwargs:
            stats=kwargs['stats']
            self.__stats__.append(loadComponent("stats",stats)(_parent=self))
                    
        self.controlPipe=Pipeline(_parent=self)
        
        self.log.debug('trying to load pipeline element messageparser')
        mparser = loadComponent("pipeelement", "MessageParserElement")(_parent=self.controlPipe)
        
        self.log.debug('trying to load pipeline element multiReceipient')
        multiparser = loadComponent("pipeelement", "MultiRecipientElement")(_parent=self.controlPipe)
        
        self.log.debug('trying to load pipeline element ack')
        ackparser = loadComponent("pipeelement", "AckElement")(_parent=self.controlPipe)
        
        self.log.debug('trying to load pipeline element headerparser')
        hparser = loadComponent("pipeelement", "HeaderParserElement")(_parent=self.controlPipe)
        
        self.log.debug('trying to load pipeline element bandwidth')
        bwid = loadComponent("pipeelement", "BandwidthElement")(_parent=self.contolPipe)
       
        
        if "control" not in kwargs:
            control = defaultControl
        else:
            control = kwargs["control"]
        c, a, k = control
        p=50028
        if "port" in kwargs:
            p=kwargs["port"]
            
        port, IF = p, ""
        if "port" in k:
            port=k["port"]
        if "interface" in k:
            IF=k["interface"]
        
        k['port']=findNextConsecutivePorts(port,IF)
        
        
        self.log.debug('trying to load pipeline element updport')
        udpparser = loadComponent("pipeelement", "UDPPortElement")(_parent=self.controlPipe,*a,**k)
        
        
        self.controlPipe.append(mparser)
        self.controlPipe.append(multiparser)
        self.controlPipe.append(ackparser)
        self.controlPipe.append(hparser)
        self.controlPipe.append(bwid)
        self.controlPipe.append(udpparser)
        
        #self.controlPipe.printall()
        #self.controlPipe.call('listen')
      
        self.initEngine(*args, **kwargs)
        
    def enableTraffic(self, **kwargs):
        ##NetworkChecker
        #self.netChecker=loadComponent('plugin','NetworkChecker')(_parent=self)
        #self.holePuncher=loadComponent('plugin','HolePuncher')(_parent=self)

        self.trafficPipe=Pipeline(_parent=self)
        
        self.log.debug('trying to load pipeline element blocksplitter')
        bsplitter = loadComponent("pipeelement", "BlockSplitterElement")(_parent=self.trafficPipe)
        self.trafficPipe.append(bsplitter)
        
        self.log.debug('trying to load pipeline element blockcache')
        bcache = loadComponent("pipeelement", "BlockCacheElement")(_parent=self.trafficPipe)
        self.trafficPipe.append(bcache)
        
        self.log.debug('trying to load pipeline element flowcontrol')
        fcontrol= loadComponent("pipeelement", "FlowControlElement")(_parent=self.trafficPipe)
        self.trafficPipe.append(fcontrol)
        
        self.log.debug('trying to load pipeline element blockheader')
        bhead = loadComponent("pipeelement", "BlockHeaderElement")(_parent=self.trafficPipe)
        self.trafficPipe.append(bhead)
        
        #self.log.debug('trying to load pipeline element bandwidth')
        #bwid = loadComponent("pipeelement", "BandwidthElement")(_parent=self.controlPipe)
        #self.trafficPipe.append(bwid)
        
        self.log.debug('trying to load pipeline element bandwidth')
        bwid = loadComponent("pipeelement", "BandwidthElement")(_parent=self.trafficPipe)
        self.trafficPipe.append(bwid)
        
        self.log.debug('trying to load pipeline element udpport')
        port = self.controlPipe.getElement("UDPPortElement").port +1 
        tport = loadComponent("pipeelement", "UDPPortElement")(_parent=self.trafficPipe, to='dataPort', port=port)
        self.trafficPipe.append(tport)
        
        #self.trafficPipe.call('listen')
        
    def enableUI(self,**kwargs):
        if 'UI' not in kwargs or not kwargs['UI']:
            return
        
        controlUI=kwargs['UI']
        c,a,k=controlUI
        self.log.debug('trying to load %s',c)
        controlUI=loadComponent('ui',c)
        self.controlUI=controlUI(remote=False,_parent=self.interface) # (_parent=self, *a, **{'remote':False})


    
    def getStream(self, streamID):
        ret = None
        for s in self.streams:
            if s.stream.id == streamID:
                ret = s
                break
        return ret 
    
    def getPStream(self, streamID):
        ret = None
        for s in self.producingStreams:
            if s.stream.id == streamID:
                ret = s
                break
        return ret
    
    def getStreamID(self, stream):
        ret = None
        for s in self.streams:
            if s.stream == stream:
                ret = s.stream.id
                break
        return ret 
    
    def getPStreamID(self, stream):
        ret = None
        for s in self.producingStreams:
            if s.stream == stream:
                ret = s.stream.id
                break
        return ret
   
   
        
    def delPStream(self, streamID):
        s=self.getPStream(streamID)
        if not s:
            pass #raise ValueError("Stream doesn't exist")
        else:
            reactor.callLater(0, self.producingStreams.remove, s)
            
    def delStream(self, streamID):
        s=self.getStream(streamID)
        if not s:
            pass #raise ValueError("Stream doesn't exist")
        else:
            reactor.callLater(0, self.streams.remove, s)
           
    def getProducingStreams(self):
        s=[s.stream for s in self.producingStreams]
        return s
    
    def getRegisteredStreams(self):
        s=[s.stream for s in self.streams]
        return s
        
    def getAllStreams(self):
        ret = []
        for s in self.streams:
            ret.append(s)
        
        for s in self.producingStreams:
            ret.append(s)
            
        return ret 

        
    @abstractmethod
    def initEngine(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def start(self):
        pass

    def quit(self,*args):
        reactor.stop()
        
        
        
  
