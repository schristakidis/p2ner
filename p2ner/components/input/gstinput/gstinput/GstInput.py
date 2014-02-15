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




import time, sys
import os
from twisted.internet import reactor,protocol
import os.path
from collections import deque
from InputProtocol import InputProto
from p2ner.abstract.input import Input


class GstInput(Input):
    def initInput(self, *args,**kwargs):
        self.hasPlayer=False


        self.playing=False
        self.buffer = ''
        self.proto=InputProto()
        cpath=os.path.dirname(os.path.realpath(__file__))
        self.path=os.path.join(cpath, "InputProcess.py")
        # self.setIF(self.type,self.filename,self.videorate)
        self.setIF(self.stream.type, self.stream.filename)# self.videorate)

    def setIF(self, type, filename=None , videorate=0, streamport=-1):
        try:
            if sys.executable.lower().endswith('p2ner.exe'):
                reactor.spawnProcess(self.proto,os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),'gstinput.exe'),(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),'gstinput.exe'),),env=None)
            else:
                reactor.spawnProcess(self.proto,sys.executable, (sys.executable,self.path),env=None)
        except:
            raise

        try:
            videorate = int(videorate)
            print videorate
        except:
            videorate = 0

        try:
            streamport = int(streamport)
            print streamport
        except:
            streamport = -1


        if 'file' in type:
            if 'win' in sys.platform:
                #no pass=qual for windows tests
                pipeline = "filesrc name=filesrc ! queue ! decodebin name=d d. !  queue ! audioconvert ! faac ! queue ! mpegtsmux name=m ! queue ! appsink name=p2sink d. ! queue !   x264enc  name=xenc byte-stream=true ! queue ! m."
            else:
                #pipeline = "filesrc name=filesrc ! queue ! decodebin name=d d. !  queue ! audioconvert ! faac ! queue ! mpegtsmux name=m ! queue ! appsink name=p2sink d. ! queue !   x264enc  name=xenc byte-stream=true ! queue ! m." #pass=qual
                pipeline = "filesrc name=filesrc ! queue  ! decodebin name=d d. !  queue ! audioconvert ! audioresample ! faac ! queue ! mpegtsmux name=m ! queue ! appsink name=p2sink d. ! queue ! ffmpegcolorspace ! videorate ! videoscale !  ffenc_mpeg4 !  queue ! m."
                print "this one"
            pipeline = "filesrc name=filesrc ! queue  ! decodebin name=d d. !  queue ! audioconvert ! audioresample ! faac ! queue ! mpegtsmux name=m ! queue ! appsink name=p2sink d. ! queue ! ffmpegcolorspace ! videorate ! videoscale !  ffenc_mpeg4 !  queue ! m."
        elif type=='stream':
            # pipeline = "udpsrc name=udpsrc ! queue ! decodebin name=d d. !  queue ! audioconvert ! faac ! queue ! mpegtsmux name=m ! queue ! appsink name=p2sink d. ! queue !  x264enc  name=xenc byte-stream=true pass=qual ! queue ! m."
            pipeline = 'udpsrc name=udpsrc caps="application/x-rtp,media=(string)video,clock-rate=(int)90000"  ! rtpmp2tdepay ! appsink name=p2sink'
        elif type=='webcam':
            if sys.platform == 'win32':
                pipeline = "ksvideosrc ! queue ! ffmpegcolorspace !  videorate ! videoscale ! queue !  x264enc byte_stream=true name=xenc pass=qual ! queue ! mux. dshowaudiosrc ! queue ! audio/x-raw-int,channels=1 ,depth=8  ! audioconvert ! queue ! faac  ! queue ! mpegtsmux name=mux  ! appsink name=p2sink"
                #No-Audio
#                pipeline = "ksvideosrc ! queue ! ffmpegcolorspace !  videorate ! videoscale ! queue ! ffenc_mpeg4 me-method=5 name=xenc ! queue  ! appsink name=p2sink"
#                pipeline = "ksvideosrc ! queue ! ffmpegcolorspace !  videorate ! videoscale ! queue ! x264enc byte_stream=true name=xenc pass=qual ! queue  ! appsink name=p2sink"
            else:
                pipeline = "v4l2src ! queue !  ffmpegcolorspace ! videorate ! videoscale ! queue !  ffenc_mpeg4 name=xenc    ! queue ! mux. alsasrc ! queue ! audio/x-raw-int,rate=8000,channels=1 ,depth=8  ! audioconvert ! audioresample ! queue ! lame  ! queue ! mpegtsmux name=mux  ! appsink name=p2sink"
        else:
            raise ValueError('unknown type:%s in GstInput',type)

        self.proto.sendData(pipeline)
        self.proto.sendData(type)
        self.proto.sendData(filename)
        # self.proto.sendData(videorate)
        self.proto.sendData(streamport)
        self.hasPlayer=True

    def start(self):
        if not self.hasPlayer:
            self.setIF(self.stream.type, self.stream.filename)# self.videorate)
        self.proto.sendData('start')
        self.playing=True

    def stop(self):
        if self.playing:
            self.playing = False
            self.hasPlayer=False
            self.proto.closeInput()


    def read(self):
        buf=self.proto.getBuffer()
        # print len(buf), "READ"
        return buf

    def isRunning(self):
        return self.playing


