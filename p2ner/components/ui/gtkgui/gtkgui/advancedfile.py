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
import os.path
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from helper import validateIp, validatePort
import getpass
from settings import SettingsGui
from converter import ConverterGui
from remotefilechooser import RemoteFileChooser
from pkg_resources import resource_string
from p2ner.abstract.ui import UI

class FileGui(UI):
    
    def initUI(self,parent):
        self.parent=parent
       
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        """
        try:
            self.builder.add_from_file(os.path.join(path,'advancedFile.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'advancedFile.glade'))
        """
        self.builder.add_from_string(resource_string(__name__, 'advancedFile.glade'))
        self.builder.connect_signals(self)
        
        self.fileEntry=self.builder.get_object('fileEntry')
        self.subsEntry=self.builder.get_object('subsEntry')
        
        self.subsButton=self.builder.get_object('subsButton')
        self.convertedButton=self.builder.get_object('convertedButton')
        self.offlineButton=self.builder.get_object('offlineButton')
        
        self.ui=self.builder.get_object('ui')
        
        self.constructEncodings()
        self.ui.show()
        
    def on_openFile_clicked(self,widget,data=None):
        if self.remote:
            self.browseRemoteFile()
        else:
            self.browseLocalFile()
            
    def browseRemoteFile(self):
        RemoteFileChooser(self.browseFinished,self.interface)
               
    def browseLocalFile(self):
        filter=gtk.FileFilter()
        filter.set_name('video files')
        filter.add_mime_type('video/*')
        filter2=gtk.FileFilter()
        filter2.set_name('avi files')
        filter2.add_pattern('*.avi')
        filter3=gtk.FileFilter()
        filter3.set_name('all files')
        filter3.add_pattern('*')
        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
       
        if 'win' not in sys.platform:
            dialog.add_filter(filter)
        dialog.add_filter(filter3)           
        dialog.add_filter(filter2)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()           
        elif response == gtk.RESPONSE_CANCEL:
            filename=None
            
        dialog.destroy()
        self.browseFinished(filename)

    def browseFinished(self,filename):
        if filename:
            self.fileEntry.set_text(filename)
                
    def on_subsButton_toggled(self,widget):
        self.builder.get_object('subsBox').set_sensitive(widget.get_active())

            
    def on_convertedButton_toggled(self,widget):
        if widget.get_active():
            self.subsButton.set_active(False)
            self.offlineButton.set_active(False)
        self.builder.get_object('subsFrame').set_sensitive(not widget.get_active())
        
    def on_offlineButton_toggled(self,widget):
        if widget.get_active():
            self.convertedButton.set_active(False)

    def on_openSubs_clicked(self,widget):
        if self.remote:
            self.browseRemoteSub()
        else:
            self.browseLocalSub()
            
    def browseRemoteSub(self):
        RemoteFileChooser(self.browseFinishedSub,self.interface)
        
    def browseLocalSub(self):
        """
        filter=gtk.FileFilter()
        filter.set_name('video files')
        filter.add_mime_type('video/*')
        filter2=gtk.FileFilter()
        filter2.set_name('avi files')
        filter2.add_pattern('*.avi')
        filter3=gtk.FileFilter()
        filter3.set_name('all files')
        filter3.add_pattern('*')
        """
        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
       
        """
        if 'win' not in sys.platform:
            dialog.add_filter(filter)
        dialog.add_filter(filter3)           
        dialog.add_filter(filter2)
        """
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()    
           
        elif response == gtk.RESPONSE_CANCEL:
            filename=None
            
        dialog.destroy()
        self.browseFinishedSub(filename)
        
    def browseFinishedSub(self,filename):
        if filename:
            self.subsEntry.set_text(filename)
            
    def constructEncodings(self):
        self.enc=self.preferences.getSubEncodings()
         
        subsBox=self.builder.get_object('encodingBox')
        self.subsCombo = gtk.combo_box_new_text()
        #self.subsCombo.set_property('width-request',100)
        subsBox.pack_start(self.subsCombo,True,True,0)
        self.subsCombo.show()
        
        found=0
        i=0
        for k in self.enc['encodings'].keys():
            self.subsCombo.append_text(k)
            if k==self.enc['default']:
                found=i
            i+=1
        self.subsCombo.set_active(found)
        
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]
    
    def on_cancelButton_clicked(self,widget):
        self.ui.destroy()
        self.parent.setAdvancedSettings(False)
        
        
    def on_okButton_clicked(self,widget):
        advSettings={}
        advSettings['filename']=self.fileEntry.get_text()
        if not advSettings['filename']:
            return
        
        advSettings['subs']=self.subsButton.get_active()
        
        if self.subsButton.get_active():
            advSettings['subsFile']=self.subsEntry.get_text()
            if not advSettings['subsFile']:
                return
            advSettings['encoding']=self.enc['encodings'][self.subsCombo.get_active_text()]
            
        advSettings['offline']=self.offlineButton.get_active()
        advSettings['converted']=self.convertedButton.get_active()
        
        self.ui.destroy()
        self.parent.setAdvancedSettings(advSettings)
        
            
    
