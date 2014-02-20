import os, sys
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


ENCODINGS={'Greek':'ISO-8859-7',
                      'Universal':'UTF-8',
                      'Western European':'Latin-9'}

class remoteproducerFrame(genericFrame):
    def initUI(self):
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'optRemote.glade'))
        self.builder.connect_signals(self)
        
        self.changeButton=self.builder.get_object('changeButton')
        self.frame=self.builder.get_object('remoteProducerFrame')
        self.checkButton=self.builder.get_object('checkRemote')
        self.checkButton.connect('toggled',self.on_check_toggled)
        self.passEntry=self.builder.get_object('passEntry')

        self.passEntry.connect('activate',self.on_pass_edited)
        self.passEntry.connect('focus-out-event',self.on_focus_out)
        self.dirEntry=self.builder.get_object('dirEntry')
        self.dirEntry.set_sensitive(False)
        
    def refresh(self):
        self.passEntry.set_sensitive(False)
        self.changeButton.set_sensitive(True)
        remotePref=self.preferences.getRemotePreferences()
        self.checkButton.set_active(remotePref['enable'])
        self.passEntry.set_text(remotePref['password'])
        self.oldPass=remotePref['password']
        self.dirEntry.set_text(remotePref['dir'])
        

    def on_check_toggled(self,widget):
        self.preferences.setEnableRemoteProducer(widget.get_active())
        
    def on_changeButton_clicked(self,widget):
        widget.set_sensitive(False)
        self.passEntry.set_sensitive(True)
        self.passEntry.set_text('')
        self.passEntry.grab_focus()
        
    def on_pass_edited(self,widget):
        self.oldPass=widget.get_text()
        self.preferences.setRemotePassword(self.oldPass)
        widget.set_sensitive(False)
        self.changeButton.set_sensitive(True)
        
    def on_focus_out(self,widget,event):
        widget.set_text(self.oldPass)
        widget.set_sensitive(False)
        self.changeButton.set_sensitive(True)
        
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
        if filename:
            self.dirEntry.set_text(filename)
            self.preferences.setRemoteProducerDir(filename)           

                
