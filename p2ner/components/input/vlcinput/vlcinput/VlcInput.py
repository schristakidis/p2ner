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
from twisted.internet import reactor, protocol
from p2ner.abstract.input import Input
from p2ner.util.utilities import vlc_path,getVlcVersion,getVlcHexVersion,getVlcReqVersion,getVlcReqHexVersion
import math
from collections import deque


vlc_defaults = {
    'win': {
            'cfile': " -I dummy  --dummy-quiet --ignore-config --sout=#duplicate{dst=standard{mux=ts{shaping=%d,use-key-frames},dst=-},dst=display{noaudio,novideo} vlc://quit",
            'file': " -I dummy --dummy-quiet --ignore-config  --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,soverlay,acodec=mp4a,ab=32,channels=2,samplerate=44100,audio-sync}:duplicate{dst=standard{mux=ts{shaping=%d,use-key-frames},dst=-},dst=display{noaudio,novideo} vlc://quit",
            'webcam': ' -I dummy --dummy-quiet --ignore-config dshow:// --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,acodec=mp4a,ab=32,channels=2,samplerate=44100,audio-sync}:standard{access=file,mux=ts{shaping=%d,use-key-frames},dst=-} vlc://quit',
            'stream': ' -I dummy --dummy-quiet --ignore-config --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,acodec=mp4a,ab=32,channels=2,samplerate=44100,audio-sync}:standard{access=file,mux=ts{shaping=%d,use-key-frames},dst=-} vlc://quit',
            'tv': " -I dummy --dummy-quiet  --ignore-config --program=%d --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,soverlay,acodec=mp4a,ab=32,channels=2,samplerate=44100,audio-sync}:duplicate{dst=standard{mux=ts{shaping=%d,use-key-frames},dst=-},dst=display{noaudio,novideo} vlc://quit"
               },
    'linux':{
            'cfile': " -I dummy --ignore-config --sout=#duplicate{dst=standard{mux=ts{shaping=%d,use-key-frames},dst=-},dst=display{noaudio,novideo} vlc://quit",
            'file': " -I dummy    --ignore-config --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,soverlay,acodec=mp4a,ab=32,channels=1,samplerate=44100}:duplicate{dst=standard{mux=ts{shaping=%d,use-key-frames},dst=-},dst=display{noaudio,novideo} vlc://quit",
            'webcam': ' -I dummy --ignore-config v4l2:// :input-slave=alsa://pulse   --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,acodec=mp4a,ab=32,audio-sync}:standard{access=file,mux=ts{shaping=%d,use-key-frames},dst=-} vlc://quit',
            'stream': ' -I dummy  --ignore-config --sout=#transcode:standard{access=file,mux=ts,dst=-} vlc://quit',
             'tv': " -I dummy   --ignore-config --program=%d --sout=#transcode{width=%d,height=%d,venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,soverlay,acodec=mp4a,ab=32,channels=1,samplerate=44100}:duplicate{dst=standard{mux=ts{shaping=%d,use-key-frames},dst=-},dst=display{noaudio,novideo} vlc://quit"
             }
    }

class VlcInput(Input):
    def initInput(self, *args,**kwargs):


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

        self.input=kwargs['input']
        self.videoRate=self.input['videoRate']
        self.hasPlayer=False


        try:
            self.videoRate= int(self.videoRate)
        except:
            self.videoRate=0

        self.height=self.input['height']
        self.width=self.input['width']

    def setIF(self, type, filename=None , videorate=0, streamport=-1, exe=None, line=None):

        try:
            streamport = int(streamport)
            if streamport<-1: streamport=-1
            print streamport
        except:
            streamport = -1

        platform = sys.platform
        if sys.platform.startswith('win'):
            self.platform=platform='win'
        if sys.platform.startswith('linux'):
            self.platform=platform='linux'

        if exe:
            if not os.path.exists(exe):
                print "invalid exe.. fall back"
                exe=None

        if not exe:
            if platform=='win':
                if vlc_path() != None:
                    exe=vlc_path() + "\\vlc.exe "
                    self.proto=vlcInputProtocol(self,self.log)
                else:
                    raise("unable to find vlc path")
            else:
                exe='vlc'

        self.proto = vlcInputProtocol(self,self.log)

        arg1=arg2=''

        if self.input['advanced'] and self.input['advanced']['subs']:
            arg1=('--sub-file=%s'%self.input['advanced']['subsFile'])
            arg2=('--subsdec-encoding=%s'%self.input['advanced']['encoding'])

        if not line:
            args=(int(self.width),int(self.height),int(videorate),int(videorate),int(self.scheduler.blocksSec))
            if type == 'webcam':
                proc = ['vlcProcess']+(vlc_defaults[platform][type]%args).split()
            elif type=='cfile':
                proc = ['vlcProcess', filename]+(vlc_defaults[platform][type]).split()
            elif type=='stream':
                proc = ['vlcProcess', filename,arg1,arg2]+(vlc_defaults[platform][type]).split()
            elif type=='tv':
                file=filename[0]
                args=(int(filename[1]),int(self.width),int(self.height),int(videorate),int(videorate),int(self.scheduler.blocksSec))
                proc = ['vlcProcess', file]+(vlc_defaults[platform][type]%args).split()
            else:
                proc = ['vlcProcess', filename,arg1,arg2]+(vlc_defaults[platform][type]%args).split()
        else:
            proc = ('vlcProcess')+line.split()

        print proc
        reactor.spawnProcess(self.proto,exe,(proc),env=None)
        #self.playing=True

        self.hasPlayer=True


    def stop(self):
        if self.playing:
            self.playing=False
            if 'win' in sys.platform:
                if vlc_path() != None:
            #   self.proc.terminate()
                    self.proto.closeVlc()
            else:
                self.proto.closeVlc()
            self.hasPlayer=False
            self.log.debug('vcl input stopped')


    def start(self):
        if not self.hasPlayer:
            self.setIF(self.stream.type,self.stream.filename,self.videoRate)
            self.log.debug('setting player in vlc input')
        self.playing=True
        self.log.debug('starting vlc input')


    def read(self):
        ret=self.proto.getBuffer()
        #print len(ret)
        return ret

    def isRunning(self):
        return self.playing


class vlcInputProtocol(protocol.ProcessProtocol):
    def __init__(self, parent,log):
        self.parent=parent
        self.stopped=False
        self.pause=False
        self.inputbuffer = ""
        self.log=log

    def closeVlc(self):
        print "should close vlc"
        try:
            self.transport.signalProcess('TERM')
            self.stopped=True
        except:
            raise
        #self.transport.loseConnection()

    def errReceived(self, data):
        #print "VLC INPUT:", data
        pass

    def outReceived(self, data):
        self.inputbuffer="".join([self.inputbuffer,data])


    def getBuffer(self):
        buf=self.inputbuffer[:]
        self.inputbuffer=''
        return buf

    def processEnded(self,status):
        print "vlc stopped"
        print status
        if not self.stopped:
            self.log.debug('vlc input has exitted')
            self.stopped=False
            self.parent.streamComponent.stop()


if __name__=='__main__':
    print 1

