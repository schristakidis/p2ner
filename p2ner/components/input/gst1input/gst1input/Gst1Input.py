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


class Gst1Input(Input):
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
                reactor.spawnProcess(self.proto,os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),'gst1input.exe'),(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),'gst1input.exe'),),env=None)
            else:
                reactor.spawnProcess(self.proto,sys.executable, (sys.executable,self.path),env=None)
        except:
            raise

        #if type=='stream':
        #    pipeline = 'udpsrc name=udpsrc caps="application/x-rtp,media=(string)video,clock-rate=(int)90000"  ! rtpmp2tdepay ! appsink name=p2sink'
        #else:
        #    raise ValueError('type:%s is not supported yet from GstInput',type)
        pipeline = "noo"

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
        reactor.callLater(20, self.proto.sendData, '5000')

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


