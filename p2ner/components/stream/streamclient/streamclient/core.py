# -*- coding: utf-8 -*-
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


from p2ner.abstract.stream import Stream
from p2ner.core.components import loadComponent
from messages.serverstarted import ServerStartedMessage, StartRemoteMessage
from messages.serverstopped import ServerStoppedMessage

defaultScheduler = ("PullClient", [], {})
defaultOverlay = ("CentralClient", [], {})


class StreamClient(Stream): 
    def initStream(self, *args, **kwargs): #stream, scheduler=defaultScheduler, overlay=defaultOverlay,producer=False):
        self.producing=False
        self.running=False
        self.log=self.logger.getLoggerChild(('c'+str(self.stream.id)),self.interface)
        self.log.info('new  stream')
        self.log.info('%s',self.stream)
        self.sanityCheck(["trafficPipe", "controlPipe", "output"])
        c,a,k=defaultOverlay
        if self.stream.overlay:
            c=self.stream.overlay['component']
        self.log.debug('trying to load %s',c)
        self.overlay = loadComponent("overlay", c)(_parent=self, *a,**k)
        c,a,k=defaultScheduler
        if self.stream.scheduler:
            c=self.stream.scheduler['component']
        self.log.debug('trying to load %s',c)
        self.scheduler = loadComponent("scheduler", c)(_parent=self,* a,**k)
        self.trafficPipe.registerProducer(self.scheduler)
        self.registerMessages()
        
    def registerMessages(self):
        self.messages = []
        self.messages.append(ServerStartedMessage())
        self.messages.append(ServerStoppedMessage())
        
    def startRemoteProducer(self):
        self.log.debug('sending startRemote message to %s',self.server)
        StartRemoteMessage.send(self.stream.id,self.server,self.controlPipe)
        
    def start(self):
        if not self.running:
            self.log.info('stream is starting')
            self.stream.live=True
            self.interface.setLiveStream(self.stream.id,True)
            self.running=True
            for c in ["output",  "scheduler"]:
                self.log.debug('trying to start %s',c)
                self[c].start()
    
    def stop(self):
        if True:#self.running:
            self.log.info('should stop stream')
            d=self['overlay'].stop()
            d.addCallback(self._stop)
            return d
        
    def _stop(self,res):
            self.log.info('stream is stopping')
            self.running=False
            self.stream.live=False
            self.interface.setLiveStream(self.stream.id,False)
            self.trafficPipe.unregisterProducer(self.scheduler)
            for c in ["output",  "scheduler"]:
                self.log.debug('trying to stop %s',c)
                self[c].stop()
            self.log.info('removing stream')
            self.root.delStream(self.stream.id)
            for c in ["output",  "scheduler",'overlay']:
                self[c].purgeNS()
            self.purgeNS()
            
