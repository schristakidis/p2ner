import pygtk
pygtk.require("2.0")
import gtk
import gobject
from p2ner.util.utilities import vlc_path
import os.path,sys
from twisted.internet import reactor,protocol

vlc_defaults = {
    'win': " -I dummy --dummy-quiet  --sout=#transcode{venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,soverlay,acodec=mp4a,ab=32,channels=2,samplerate=44100,audio-sync}:standard{access=file,mux=ts,dst=-} vlc://quit",            
    'linux': " -I dummy   --sout=#transcode{venc=x264{slice-max-size=25200,keyint=60,vbv-maxrate=%d,ratetol=0},vcodec=h264,vb=%d,scale=1,soverlay,acodec=mp4a,ab=32,channels=1,samplerate=44100}:standard{access=file,mux=ts,dst=-} vlc://quit"
    }
                


class Converter(object):
    def __init__(self):
        pass
        
    def startConverting(self,dir,filename,videoRate,subs,subsFile,subsEnc):
        self.progress=0
        
        if sys.platform.startswith('win'):
            if vlc_path() != None:
                exe=vlc_path() + "\\vlc.exe "
                self.proto=vlcInputProtocol(self)
            else:
                raise("unable to find vlc path")
            pipeline=vlc_defaults['win']
        else:
            exe='vlc'
            pipeline=vlc_defaults['linux']
        
        self.dest=os.path.join(dir,os.path.basename(filename))
        
        self.proto = vlcInputProtocol(self,self.dest)        
        
        arg1=arg2=''
            
        if subs:
            arg1=('--sub-file=%s'%subsFile)
            arg2=('--subsdec-encoding=%s'%subsEnc)
            
            
        args=(int(videoRate),int(videoRate))
        #line = str(pipeline%args).split()
        proc = ['vlcProcess', filename,arg1,arg2]+(pipeline%args).split()
        reactor.spawnProcess(self.proto,exe,(proc),env=None)
        
        
    def abort(self):
        self.proto.closeVlc()
        os.remove(self.dest)
        self.progress=-2
        
    def finished(self):
        self.proto.closeFile()
        self.progress=-1
        
    def getStatus(self):
        return self.progress
        
class vlcInputProtocol(protocol.ProcessProtocol):
    def __init__(self, parent,dest):
        self.parent=parent
        self.len=0
        self.f=open(dest,'wb')
        self.live=True

    def outReceived(self, data):
        try:
            self.f.write(data)
            self.len +=len(data)
            s=self.len/(1024**2)
            self.parent.progress=str(s)
        except:
            pass

    def closeVlc(self):
        self.live=False
        self.transport.signalProcess('TERM')
        self.f.close()
        
    def closeFile(self):
        self.f.close()
    
    def errReceived(self, data):
        #print "VLC INPUT:", data
        pass

    def processEnded(self,status):
        #print status
        if self.live:
            self.f.flush()
            self.f.close()
            self.parent.finished()
        