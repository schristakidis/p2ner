# -*- coding: utf-8 -*-
from twisted.internet import reactor
from time import localtime,mktime
from p2ner.abstract.stream import Stream
from p2ner.core.components import loadComponent
from messages.serverstarted  import ServerStartedMessage,ServerStoppedMessage


defaultScheduler = ("SimpleProducer", [], {})
defaultOverlay = ("CentralProducerClient", [], {})
defaultInput = ("RandomInput", [], {})

class StreamProducer(Stream):    
    def initStream(self, *args, **kwargs): 
        self.log=self.logger.getLoggerChild(('p'+str(self.stream.id)),self.interface)
        self.log.info('new producer stream')
        self.log.info('%s',self.stream)
        self.running=False
        self.producing=True
        self.sanityCheck(["trafficPipe", "controlPipe", "output"])
        c,a,k=defaultOverlay
        #if self.stream.overlay:
        #    c=self.stream.overlay['component']
        self.log.debug('trying to load %s',c)
        self.overlay = loadComponent("produceroverlay", c)(_parent=self, *a,**k)
        c,a,k=defaultScheduler
        self.log.debug('trying to load %s',c)
        self.scheduler = loadComponent("producer", c)(_parent=self,* a,**k)
        self.trafficPipe.registerProducer(self.scheduler)
        
            
        self.startMessage=ServerStartedMessage()
        
        if self.stream.startTime:
            self.log.info('stream should start after %f secs',self.stream.startTime-mktime(localtime()))
            reactor.callLater(self.stream.startTime-mktime(localtime()),self.start)
        
    def start(self):
        if not self.running:
            self.log.info('stream is started')
            self.log.debug('sending serverStarted message to %s',self.server)
            self.startMessage.send(self.stream.id, self.server, self.controlPipe)
            
    def run(self):
        if not self.running:
            self.log.info('stream should start running')
            self.stream.live=True
            self.interface.setLiveProducer(self.stream.id,True)
            self.running=True
            for c in [ "input", "output", "scheduler"]:
                self.log.debug('%s should start running',c)
                self[c].start()

    def stop(self):
        self.log.info('stopping stream')
        self.log.debug('sending serverStopped message to %s',self.server)
        ServerStoppedMessage.send(self.stream.id,self.stream.republish, self.server, self.controlPipe)
        if True: #self.running:
            for c in [ "scheduler", "overlay", "input", "output"]:
                self.log.debug('should stop %s',c)
                self[c].stop()
        
        if self.stream.republish:
            self.log.info('stream is republished')
            self.stream.live=False
            self.interface.setLiveProducer(self.stream.id,False)
            self.running=False
        else:
            self.log.info('deleting stream %d from producing streams',self.stream.id)
            #del self.log, self.startMessage, self.scheduler, self.overlay
            #if 'input' in self:
            #    del self.input
            #if 'output' in self:
            #    del self.output
            self.root.delPStream(self.stream.id)
            self.interface.removeProducer(self.stream.id)
            self.trafficPipe.unregisterProducer(self.scheduler)
            for c in [ "scheduler", "overlay", "input", "output"]:
                self[c].purgeNS()
            self.purgeNS()
