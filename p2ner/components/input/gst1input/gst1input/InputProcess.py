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

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import sys
from collections import deque
import select
Gst.init(None)

class AudioEncoder(Gst.Bin):
    def __init__(self):
        super(AudioEncoder, self).__init__()

        # Create elements
        q1 = Gst.ElementFactory.make('queue', None)
        resample = Gst.ElementFactory.make('audioresample', None)
        convert = Gst.ElementFactory.make('audioconvert', None)
        rate = Gst.ElementFactory.make('audiorate', None)
        enc = Gst.ElementFactory.make('faac', None)
        q2 = Gst.ElementFactory.make('queue', None)

        # Add elements to Bin
        self.add(q1)
        self.add(resample)
        self.add(convert)
        self.add(rate)
        self.add(enc)
        self.add(q2)

        # Link elements
        q1.link(resample)
        resample.link(convert)
        convert.link(rate)
        rate.link(enc)
        rate.link_filtered(enc,
            Gst.caps_from_string('audio/x-raw,channels=2')
        )
        enc.link(q2)

        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('sink', q1.get_static_pad('sink'))
        )
        self.add_pad(
            Gst.GhostPad.new('src', q2.get_static_pad('src'))
        )

class VideoEncoder(Gst.Bin):
    def __init__(self):
        super(VideoEncoder, self).__init__()

        # Create elements
        q1 = Gst.ElementFactory.make('queue', None)
        convert = Gst.ElementFactory.make('videoconvert', None)
        scale = Gst.ElementFactory.make('videoscale', None)
        enc = Gst.ElementFactory.make('x264enc', None)
        q2 = Gst.ElementFactory.make('queue', 'q2')
        self.enc = enc

        # Add elements to Bin
        print q1
        self.add(q1)
        self.add(convert)
        self.add(scale)
        self.add(enc)
        self.add(q2)

        # Set properties
        scale.set_property('method', 3)  # lanczos, highest quality scaling

        # Link elements
        q1.link(convert)
        convert.link(scale)
        scale.link_filtered(enc,
            Gst.caps_from_string('video/x-raw, width=640, height=480')
        )
        enc.link(q2)

        # Add Ghost Pads
        self.add_pad(
            Gst.GhostPad.new('sink', q1.get_static_pad('sink'))
        )
        self.add_pad(
            Gst.GhostPad.new('src', q2.get_static_pad('src'))
        )

class Encoder(object):
    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline()
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)
        self.bus.connect('message::error', self.on_error)

        # Create elements
        self.src = Gst.ElementFactory.make('filesrc', None)
        self.dec = Gst.ElementFactory.make('decodebin', None)
        self.video = VideoEncoder()
        self.audio = AudioEncoder()
        self.mux = Gst.ElementFactory.make('mpegtsmux', None)
        self.tsparse = Gst.ElementFactory.make('tsparse', None)
        self.sink =  Gst.ElementFactory.make('appsink', None)

        # Add elements to pipeline
        self.pipeline.add(self.src)
        self.pipeline.add(self.dec)
        self.pipeline.add(self.video)
        self.pipeline.add(self.audio)
        self.pipeline.add(self.mux)
        self.pipeline.add(self.tsparse)
        self.pipeline.add(self.sink)

        # Set properties
        filename = "/xtra/NCIS.6x03.Scandali.A.Washington.ITA.DVDMux.XviD-NovaRip.avi"
        self.src.set_property('location', filename)
        self.sink.set_property('max-buffers', 20)
        self.sink.set_property('emit-signals', True)
        self.video.enc.set_property('bitrate', 200)

        # Connect signal handlers
        self.dec.connect('pad-added', self.on_pad_added)
        self.sink.connect('new-sample', self.on_new_sample)

        # Link elements
        self.src.link(self.dec)
        self.video.link(self.mux)
        self.audio.link(self.mux)
        self.mux.link(self.tsparse)
        self.tsparse.link(self.sink)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def kill(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

    def on_pad_added(self, element, pad):
        string = pad.query_caps(None).to_string()
        sys.stderr.write("on_pad_added(): %s\n"%string)
        if string.startswith('audio/'):
            pad.link(self.audio.get_static_pad('sink'))
        elif string.startswith('video/'):
            pad.link(self.video.get_static_pad('sink'))

    def on_new_sample(self, appsink):
        new_sample = appsink.emit('pull-sample')
        buf = new_sample.get_buffer()
        sys.stdout.write(str(buf.extract_dup(0,buf.get_size())))
        sys.stdout.flush()
        r, w, e = select.select([ sys.stdin ], [], [], 0)
        if sys.stdin in r:
            try:
                videorate = int(sys.stdin.readline().rstrip())
                self.video.enc.set_property('bitrate', videorate)
            except:
                sys.stderr.write("received wrong videorate\n")


    def on_eos(self, bus, msg):
        sys.stderr.write("on_eos\n")
        self.kill()

    def on_error(self, bus, msg):
        sys.stderr.write("on_error(): %s\n"%msg.parse_error())
        self.kill()


class GstPipeline(object):
    def __init__(self):
        self.inBuffer=deque()

    def start(self):
        sys.stderr.flush()

        pipeline = sys.stdin.readline().rstrip()
        sys.stderr.write(pipeline)
        type = sys.stdin.readline().rstrip()
        filename=sys.stdin.readline().rstrip()
        sys.stderr.write(filename)
        # videorate = int(sys.stdin.readline().rstrip())
        streamport = float(sys.stdin.readline().rstrip())
        self.pipeline = Encoder()
        #self.recorder=gst.parse_launch(pipeline)
        #if type=='file':
        #    fn = self.recorder.get_by_name('filesrc')
        #    fn.set_property("location",filename)

        #if videorate>0:
        #    xenc=self.recorder.get_by_name('xenc')
        #    xenc.set_property('bitrate',videorate)

        #if type=='stream':
        #    portNumber=filename.split(':')[-1]
        #    port=self.recorder.get_by_name('udpsrc')
        #    port.set_property('port',int(portNumber))
        #    # port.set_property('port',streamport)#

        #self.appsink = self.recorder.get_by_name('p2sink')
        #self.appsink.set_property('emit-signals', True)
        #self.appsink.connect('new-buffer', self.new_buffer)

        #self.recorder.set_state(gst.STATE_NULL)
        self.waitStart()

    def waitStart(self):
        wait = sys.stdin.readline().rstrip()
        if wait=='start':
            self.startPlaying()
        else:
            sys.stderr.write(wait)

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
        self.pipeline.run()




if __name__=='__main__':
    GstPipeline().start()
