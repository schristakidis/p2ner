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



import pygst
pygst.require("0.10")
import gst
import os.path, sys
from twisted.internet import reactor, defer,protocol
from p2ner.abstract.output import Output
# from OutputProtocol import OutputProto

class GstOutput(Output):
    def initOutput(self, *args, **kwargs):
        self.log.debug('gst output loaded')
        self.playing=False
        self.buffer=''
        self.hasPlayer=False
        # cpath=os.path.dirname(os.path.realpath(__file__))
        # self.path=os.path.join(cpath, "OutputProcess.py")
        # self.proto=OutputProto()

    def startProto(self):
        # reactor.spawnProcess(self.proto,sys.executable, (sys.executable,self.path),env=None)
        pipe = "appsrc name=appsrc ! rtpmp2tpay ! queue ! udpsink host=127.0.0.1 port=1234"
        self.player=gst.parse_launch(pipe)
        self.appsink = self.player.get_by_name('appsrc')
        self.appsink.set_property('emit-signals', True)
        # self.proto.sendData(pipe)
        self.player.set_state(gst.STATE_NULL)
        bus = self.player.get_bus()
        #bus.connect('message', self.on_message)
        #bus.add_signal_watch()
        bus.enable_sync_message_emission()
        self.hasPlayer=True

    def cleanup(self):
        pass

    def stop(self):
        if self.playing:
            self.playing=False
            self.hasPlayer=False
            # self.proto.closeOutput()
            self.log.debug('gst output is closing')
            self.player.set_state(gst.STATE_NULL)

    def start(self):
        if not self.hasPlayer:
            self.startProto()
        self.player.set_state(gst.STATE_PLAYING)
        # self.proto.sendData('start')
        self.playing=True
        self.log.info('pure vlc output initting')

    def write(self,block):
        if not self.playing:
            self.playing=True
            self.log.debug('pure vlc output is starting')
            self.player.set_state(gst.STATE_PLAYING)
        # self.proto.sendData(block)
        self.appsink.emit('push-buffer', gst.Buffer(block))

    def isRunning(self):
        return self.playing


