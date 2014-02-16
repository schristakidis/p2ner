from twisted.internet import gtk2reactor
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

gtk2reactor.install()
from twisted.internet import reactor,task
import pygst
pygst.require("0.10")
import gst
import sys
from collections import deque


class GstPipeline(object):
    def __init__(self):
        self.inBuffer=deque()



    def start(self):
        sys.stderr.flush()

        pipeline = sys.stdin.readline().rstrip()
        sys.stderr.write(pipeline)
        type=sys.stdin.readline().rstrip()
        filename=sys.stdin.readline().rstrip()
        sys.stderr.write(filename)
        # videorate = int(sys.stdin.readline().rstrip())
        streamport =float(sys.stdin.readline().rstrip())
        self.pipeline = gst.Pipeline()
        self.recorder=gst.parse_launch(pipeline)
        if type=='file':
            fn = self.recorder.get_by_name('filesrc')
            fn.set_property("location",filename)

        #if videorate>0:
        #    xenc=self.recorder.get_by_name('xenc')
        #    xenc.set_property('bitrate',videorate)

        if type=='stream':
            port=self.recorder.get_by_name('udpsrc')
            port.set_property('port',5004)
            # port.set_property('port',streamport)

        self.appsink = self.recorder.get_by_name('p2sink')
        self.appsink.set_property('emit-signals', True)
        self.appsink.connect('new-buffer', self.new_buffer)

        self.recorder.set_state(gst.STATE_NULL)
        self.waitStart()

    def waitStart(self):
        wait = sys.stdin.readline().rstrip()
        if wait=='start':
            self.startPlaying()
        else:
            sys.stderr.write(wait)


    def new_buffer(self, sink):
        a=self.appsink.emit('pull_buffer')
        sys.stdout.write(str(a))
        sys.stdout.flush()


    def wait(self):
        while True:
            wait = sys.stdin.readline().rstrip()
            buf=''
            sys.stdout.writelines(self.inBuffer)
            for i in range(len(self.inBuffer)):
                self.inBuffer.popleft()
            sys.stdout.write(buf)
            sys.stdout.flush()




    def startPlaying(self):
        self.recorder.set_state(gst.STATE_PLAYING)




if __name__=='__main__':
    reactor.callLater(0.001,GstPipeline().start)
    reactor.run()
