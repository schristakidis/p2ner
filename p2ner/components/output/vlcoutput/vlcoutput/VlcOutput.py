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
import pygtk
pygtk.require('2.0')
import gtk
from twisted.internet import reactor, defer,protocol
import socket
from p2ner.abstract.output import Output
from p2ner.util.utilities import vlc_path,getVlcVersion,getVlcHexVersion,getVlcReqVersion,getVlcReqHexVersion

class VlcOutput(Output):
    def initOutput(self, *args, **kwargs):
       
       
        self.port=self.findPort()
        pipe = "appsrc name=appsrc !mpegtsparse ! rtpmp2tpay ! queue ! udpsink host=127.0.0.1 port="+str(self.port)

        self.player=gst.parse_launch(pipe)

        self.appsrc=self.player.get_by_name('appsrc')
        self.appsrc.props.format = 4

        self.playing=False
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
        print "pipeline cleanup"
        self.player.set_state(gst.STATE_NULL)
        


    def stop(self):
        if self.playing:
            self.playing=False
            print 'close output'
            self.cleanup()
            if sys.platform == 'win32':
                if vlc_path() != None:
            #   self.proc.terminate()
                    self.proto.closeVlc()                    
            else:
                self.proto.closeVlc() 


    def findPort(self):
        port=20011
        while True:
            try:
                self.fd=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                self.fd.bind(('127.0.0.1',port))
                #fd.close()
                break
            except:
                port +=1

        return port

    def start(self):
        self.player.set_state(gst.STATE_PLAYING)
        proc='vlcProcess','rtp://@:'+str(self.port)
        self.fd.close()
        if 'win' in sys.platform:
            if vlc_path() != None:
                exe=vlc_path() + "\\vlc.exe "
                self.proto=vlcProtocol(self.player,self)
        else:
            exe='vlc'
            self.proto=vlcProtocol(self.player,self)
        
        reactor.spawnProcess(self.proto,exe,(proc),env=None)
        self.playing=True
        
    def write(self,block):
        """
        if not self.playing:
            self.player.set_state(gst.STATE_PLAYING)
            self.playing=True
        """
        self.appsrc.emit('push-buffer', gst.Buffer(block))

    def isRunning(self):
        return self.playing

        
class vlcProtocol(protocol.ProcessProtocol):
    def __init__(self,player,parent):
        self.player=player
        self.parent=parent
        self.stopped=False
    def closeVlc(self):
        print "should close vlc"
        try:
            self.transport.signalProcess('TERM')
            self.stopped=True
        except:
            pass
        #self.transport.loseConnection()

    def processExited(self,status):
        print "vlc stopped"
        print status
        if not self.stopped:
            self.stopped=False
            self.player.set_state(gst.STATE_NULL)
            self.parent.streamComponent.stop()

