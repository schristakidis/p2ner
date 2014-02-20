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
from p2ner.util.utilities import get_user_data_dir
from pkg_resources import resource_string
from gtkgui.remotefilechooser import RemoteFileChooser

class generalFrame(genericFrame):
    def initUI(self):
        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'optGeneral.glade'))
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('generalFrame')

        self.checkButton=self.builder.get_object('checkButton')
        self.checkNetButton=self.builder.get_object('checkNetGui')
        self.builder.get_object('dirEntry').set_sensitive(False)
        self.constructSubs() 
        self.refresh()
        
    def refresh(self):
        self.checkButton.set_active(self.preferences.getCheckAtStart())  
        self.checkNetButton.set_active(self.preferences.getCheckNetAtStart()) 
        self.builder.get_object('dirEntry').set_text(self.preferences.getCDir())

    def on_checkNetGui_toggled(self,widget):
        self.preferences.setCheckNetAtStart(widget.get_active())
        
    def on_checkButton_toggled(self,widget):
        self.preferences.setCheckAtStart(widget.get_active())
        
        
    def getCheckAtStart(self):
        return self.checkButton.get_active()
    
    def getCheckNetAtStart(self):
        return self.checkNetButton.get_active()
        
    def on_openButton_clicked(self,widget):
        if self.remote:
            RemoteFileChooser(self.browseFinished,self.interface,onlyDir=True)
        else:
            self.browseLocally()
            
    def browseLocally(self):
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
            self.browseFinished(filename)    
            
        elif response == gtk.RESPONSE_CANCEL:
            filename=None

        
        dialog.destroy()
        
        
    def browseFinished(self,filename):
        print filename
        if filename:
            self.builder.get_object('dirEntry').set_text(filename)
            self.preferences.setConvertedDir(filename)
            
    def constructSubs(self):
        subs=self.preferences.getSubEncodings()
        
        subsBox=self.builder.get_object('subsCombo')
        self.subsCombo = gtk.combo_box_new_text()
        self.subsCombo.connect('changed',self.on_subs_changed)
        self.subsCombo.set_property('width-request',100)
        subsBox.pack_start(self.subsCombo,True,True,0)
        self.subsCombo.show()
        
        found=0
        i=0
        for k in subs['encodings'].keys():
            self.subsCombo.append_text(k)
            if k==subs['default']:
                found=i
            i+=1
        self.subsCombo.set_active(found)
        
    def on_subs_changed(self,widget):
        d=self.get_active_text(self.subsCombo)
        if d:
            self.preferences.setTempSubEncoding(d)
        
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]
    
    def on_subsButton_clicked(self,wdiget):
        d=self.get_active_text(self.subsCombo)
        if d:
            self.preferences.setSubEncoding(d)

                
