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
from generic import genericFrame
import p2ner.util.config as config

class upnpFrame(genericFrame):
    def __init__(self,parent=None):
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'optUPNP.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'optUPNP.glade'))
        
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('upnpFrame')
        
        try:
            check=config.config.getboolean('UPNP','on')
        except:
            check=True
            
        self.checkButton=self.builder.get_object('checkButton')
        
        self.checkButton.set_active(check)  

    def save(self):
        config.config.set('UPNP','on',self.checkButton.get_active())
