# -*- coding: utf-8 -*-

import os.path, sys
from twisted.internet import reactor, defer,protocol
import socket
from p2ner.abstract.output import Output
from p2ner.util.utilities import vlc_path,getVlcVersion,getVlcHexVersion,getVlcReqVersion,getVlcReqHexVersion

class PureVlcOutput(Output):
    def initOutput(self, *args, **kwargs):
        self.log.debug('pure vlc output loaded')
        self.playing=False
        
        try:
            self.so=kwargs['output']['sout']['value']
        except:
            self.so=None
            
        if not vlc_path():
            self.log.error('vlc is not installed')
            reactor.callLater(0,self.streamComponent.stop)
            self.interface.displayError('you need to install vlc player')
            return
        
        if getVlcHexVersion()<getVlcReqHexVersion():
            self.log.error('the version of vlc is wrong')
            reactor.callLater(0,self.streamComponent.stop)
            self.interface.displayError('version %s of vlc is old.\n version %s or greater is needed'%(getVlcVersion(),getVlcReqVersion()))
            return
        
    def cleanup(self):
        pass

    def stop(self):
        if self.playing:
            self.playing=False
            if 'win' in sys.platform:
                if vlc_path() != None:
                    self.proto.closeVlc()                    
            else:
                self.proto.closeVlc()                
            self.log.debug('pure vlc output is closing')

    def start(self):
                
        if self.so and len(self.so):
            so = "".join(["--sout=", self.so])
        else:
            so = ''
        
        proc='vlcProcess','-' , '--ignore-config', so, 'vlc://quit'
        if 'win' in sys.platform:
            if vlc_path() != None:
                proc='vlcProcess','-' , '-I', 'dummy-quiet',  so, 'vlc://quit'
                exe=vlc_path() + "\\vlc.exe "
                self.proto=vlcProtocol(self,self.log)
        else:
            exe='vlc'
            self.proto=vlcProtocol(self,self.log)
        
        reactor.spawnProcess(self.proto,exe,(proc),env=None)
        #self.playing=True
        self.log.info('pure vlc output initting')
        
    def write(self,block):
        if not self.playing:
            self.playing=True
            self.log.debug('pure vlc output is starting')
        self.proto.write(block)

    def isRunning(self):
        return self.playing

        
class vlcProtocol(protocol.ProcessProtocol):
    def __init__(self,parent,log):
        self.parent=parent
        self.stopped=False
        self.log=log
    
    def write(self, data):
        self.transport.write(data)
    
    def errReceived(self, data):
        #print "PURE VLC OUTPUT:", data
        if 'failure' in data and 'window' in data:
            if not self.stopped:
                self.stopped=False
                self.parent.streamComponent.stop()
                self.log.debug('pure vlc output is exiting in protocol because of an error')
                
    def closeVlc(self):
        #print "should close vlc"
        try:
            self.transport.signalProcess('TERM')
            self.stopped=True
            self.log.debug('pure vlc output is closing in protocol')
        except:
            pass
        #self.transport.loseConnection()

    def processExited(self,status):
        #print "vlc stoppedwwwwwww"
        #print status
        if not self.stopped:
            self.stopped=False
            self.parent.streamComponent.stop()
            self.log.debug('pure vlc output exitted in protocol')
