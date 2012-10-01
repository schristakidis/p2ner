from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor,task
import pygst
print "import"
pygst.require("0.10")
import gst
import sys
from collections import deque



class GstPipeline(object):    
    def __init__(self):
        self.inBuffer=deque()
        #sys.stderr.write("new input processssssssssss")
        #sys.stderr.flush()
       
        

    def start(self):
        sys.stderr.write("waitingggggggggggggggggggggggggggggggggggggggggggggg")
        sys.stderr.flush()
        
        pipeline = sys.stdin.readline().rstrip()
        type=sys.stdin.readline().rstrip()
        filename=sys.stdin.readline().rstrip()
        videorate = int(sys.stdin.readline().rstrip())
        streamport =float(sys.stdin.readline().rstrip())
        
        """
        sys.stderr.write("got arguments in input process\n")
        sys.stderr.write(pipeline)
        sys.stderr.write(type)
        sys.stderr.write(filename)
        sys.stderr.write(str(videorate))
        sys.stderr.write(str(streamport))

        sys.stderr.write('-----------------------------------------------------------------------------------------------')
        sys.stderr.flush()
        """
   
        self.pipeline = gst.Pipeline()
        self.recorder=gst.parse_launch(pipeline)
        if type=='file':
            fn = self.recorder.get_by_name('filesrc')
            fn.set_property("location",filename)

        if videorate>0:
            xenc=self.recorder.get_by_name('xenc')
            xenc.set_property('bitrate',videorate)

        if type=='stream':
            port=self.recorder.get_by_name('udpsrc')
            port.set_property('port',streamport)

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
        sys.stderr.write('starting pipilineeeeeeeeeeeee')
        self.recorder.set_state(gst.STATE_PLAYING)    

  

      
if __name__=='__main__':
     reactor.callLater(0.001,GstPipeline().start) 
     reactor.run()  