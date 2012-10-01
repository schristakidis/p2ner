import os, sys
from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except:
    pass
import pygtk
from twisted.internet import reactor
pygtk.require("2.0")
import gtk
import gobject

class genericFrame(object):
    def __init__(self,parent=None):
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'generic.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'generic.glade'))
        
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('componentsFrame')
        
    def getFrame(self):
        return self.frame
    
    def refresh(self):
        pass
    
    def save(self):
        pass
    
    def setDefaults(self):
        pass
    
