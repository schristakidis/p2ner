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


import os.path, sys
from twisted.internet import reactor, defer,protocol
import socket
from p2ner.abstract.output import Output
from p2ner.util.utilities import vlc_path,getVlcVersion,getVlcHexVersion,getVlcReqVersion,getVlcReqHexVersion
from webserver import WebUI
class FlvOutput(Output):
    def initOutput(self, *args, **kwargs):
        self.log.debug('flv vlc output loaded')
        self.playing=False
        self.web=WebUI(_parent=self.root)
        """
        try:
            self.so=kwargs['output']['sout']['value']
        except:
            self.so=None
        """
            
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
            self.web.stop()
            if 'win' in sys.platform:
                if vlc_path() != None:
                    self.proto.closeVlc()                    
            else:
                self.proto.closeVlc()                
            self.log.debug('flv vlc output is closing')

    def start(self):
        """        
        if self.so and len(self.so):
            so = "".join(["--sout=", self.so])
        else:
            so = ''
        """
        so="--sout=#transcode{width=320,height=200,venc=x264{slice-max-size=25200,keyint=60,ratetol=0},vcodec=h264,scale=1,soverlay,acodec=mp4a,ab=32,channels=1,samplerate=44100}:standard{access=http{mime=video/x-flv},mux=ffmpeg{mux=flv},dst=0.0.0.0:12000/flow.flv} "
        proc='vlcProcess','-' , '--ignore-config', so, 'vlc://quit' 
        if 'win' in sys.platform:
            if vlc_path() != None:
                proc='vlcProcess','-' , '-I', 'dummy-quiet',  so, 'vlc://quit'
                exe=vlc_path() + "\\vlc.exe "
                self.proto=vlcProtocol(self,self.log)
        else:
            exe='cvlc'
            self.proto=vlcProtocol(self,self.log)
        
        reactor.spawnProcess(self.proto,exe,(proc),env=None)
        #self.playing=True
        self.log.info('flv vlc output initting')
        
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
                self.log.debug('flv vlc output is exiting in protocol because of an error')
                
    def closeVlc(self):
        #print "should close vlc"
        try:
            self.transport.signalProcess('TERM')
            self.stopped=True
            self.log.debug('flv vlc output is closing in protocol')
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
