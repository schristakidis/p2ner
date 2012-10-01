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
from p2ner.util.utilities import get_user_data_dir

ENCODINGS={'Greek':'ISO-8859-7',
                      'Universal':'UTF-8',
                      'Western European':'Latin-9'}

class remoteproducerFrame(genericFrame):
    def __init__(self,parent=None):
        self.parent=parent
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'optRemote.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'optRemote.glade'))
        
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('remoteProducerFrame')
        
        remotePref=config.getRemotePreferences()

        self.checkButton=self.builder.get_object('checkRemote')
        self.checkButton.set_active(remotePref['enable']) 

        self.builder.get_object('dirEntry').set_text(remotePref['dir'])
        self.builder.get_object('passEntry').set_text(remotePref['password'])
        
            
    def save(self):
        config.setRemotePreferences(self.checkButton.get_active(),self.builder.get_object('dirEntry').get_text(),self.builder.get_object('passEntry').get_text())


     
    def getCdir(self):
        return self.builder.get_object('dirEntry').get_text()
    
    def on_openButton_clicked(self,widget):

        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            #print dialog.get_filename(), 'selected'
            filename = dialog.get_filename()           
            self.builder.get_object('dirEntry').set_text(filename)
        elif response == gtk.RESPONSE_CANCEL:
            filename=None

        
        dialog.destroy()
        

                