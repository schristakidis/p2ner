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

class generalFrame(genericFrame):
    def __init__(self,parent=None):
        self.parent=parent
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'optGeneral.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'optGeneral.glade'))
        
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('generalFrame')
        
        try:
            check=config.config.getboolean('General','checkAtStart')
        except:
            check=False
            
        self.checkButton=self.builder.get_object('checkButton')
        self.checkButton.set_active(check)  
        
        checkNet=config.getCheckNetMessages()
        self.checkNetButton=self.builder.get_object('checkNetGui')
        self.checkNetButton.set_active(checkNet) 

        if config.config.has_option('General','cdir'):
            self.builder.get_object('dirEntry').set_text(config.config.get('General','cdir'))
        else:
            self.builder.get_object('dirEntry').set_text(get_user_data_dir())
        
        self.constructSubs()    
            
    def save(self):
        config.config.set('General','checkAtStart',self.checkButton.get_active())
        config.config.set('General','shownetmessages',self.checkNetButton.get_active())
        config.config.set('General','cdir',self.builder.get_object('dirEntry').get_text())
        
    def getCheckAtStart(self):
        return self.checkButton.get_active()
    
    def getCheckNetAtStart(self):
        return self.checkNetButton.get_active()
    
    def setCheckNetAtStart(self,check):
        check=not check
        if check!=self.checkNetButton.get_active():
            self.checkNetButton.set_active(check)
            config.setCheckNetAtStart(check)
     
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
        
        
    def constructSubs(self):
        if config.config.has_option('General','subsencoding'):
           self.dsubs=config.config.get('General','subsencoding')
        else:
            self.dsubs='Greek'
         
        subsBox=self.builder.get_object('subsCombo')
        self.subsCombo = gtk.combo_box_new_text()
        self.subsCombo.set_property('width-request',100)
        subsBox.pack_start(self.subsCombo,True,True,0)
        self.subsCombo.show()
        
        found=0
        i=0
        for k in ENCODINGS.keys():
            self.subsCombo.append_text(k)
            if k==self.dsubs:
                found=i
            i+=1
        self.subsCombo.set_active(found)
        
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]
    
    def on_subsButton_clicked(self,wdiget):
        d=self.get_active_text(self.subsCombo)
        if d:
            config.config.set('General','subsencoding',d)
            self.dsubs=d
            
    def getSubEncodings(self):
        ret={}
        ret['default']=self.dsubs
        ret['encodings']=ENCODINGS
        return ret
                