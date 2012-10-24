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
from advancedfile import FileGui
from pkg_resources import resource_string

class ProducerGui(object):
    
    def __init__(self,parent):
        self.parent=parent
        self.gotSettings=False
        self.source='webcam'
        self.advSettings=False
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        """
        try:
            self.builder.add_from_file(os.path.join(path,'producer.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'producer.glade'))
        """
        self.builder.add_from_string(resource_string(__name__, 'producer.glade'))
        self.builder.connect_signals(self)

        self.servers=self.getServers()
        
      
        portListstore=gtk.ListStore(str)
        self.portCombo = gtk.ComboBoxEntry(portListstore, 0)
        portBox = self.builder.get_object("portBox")
        self.portCombo.set_property('width-request',80)
        portBox.pack_start(self.portCombo,True,True,0)
        
        self.portCombo.show()  
        
     
        servListstore=gtk.ListStore(str)

        for s in self.servers.keys():
            servListstore.append([s])
        
        
        self.ipCombo = gtk.ComboBoxEntry(servListstore, 0)
        self.ipCombo.child.connect('changed', self.ip_changed_cb)
        self.ipCombo.set_property('width-request',150)
        ipBox = self.builder.get_object("ipBox")
        ipBox.pack_start(self.ipCombo,True,True,0)
        self.ipCombo.show()  


        dip=self.parent.preferences.getDefaultServer()
        i=0
        found=0
        for k,v in self.servers.items():
            if dip==k:
                    found=i
            i+=1
            
        if self.servers:
            self.ipCombo.set_active(found)
        
        streamBox=self.builder.get_object('streamBox')
        self.streamCombo=gtk.combo_box_new_text()
        streamBox.pack_start(self.streamCombo,True,True,0)
       
        for p in ('http','udp','rtp'):
            self.streamCombo.append_text(p)
        
        self.streamCombo.connect('changed', self.stream_changed_cb)    
        self.streamCombo.set_active(0)
        self.streamCombo.show()
        
        channelsBox=self.builder.get_object('channelsCombo')
        self.channelsCombo=gtk.combo_box_new_text()
        channelsBox.pack_start(self.channelsCombo,True,True,0)
       
        self.channels=self.parent.preferences.getChannels()
        
        if self.channels:
            for ch in self.channels:
                self.channelsCombo.append_text(ch)
        
                self.channelsCombo.connect('changed', self.dvb_changed_cb)    
                #self.channelsCombo.set_active(0)
                self.channelsCombo.show()
        else:
            self.builder.get_object('dvbButton').set_sensitive(False)
        
        self.ui=self.builder.get_object('ui')
        self.ui.show()    
        
        self.builder.get_object('author').set_text(getpass.getuser())
      
        
    def getServers(self):
        srv=self.parent.preferences.getServers()
        servers={}
        for s in srv:
            if not servers.has_key(s[0]):
                servers[s[0]]=[]
            servers[s[0]].append(s[1])
        return servers
     
    def ip_changed_cb(self,entry):
        en=entry.get_text()
        model=self.portCombo.get_model()
        model.clear()
        if self.servers.has_key(en):
            for port in self.servers[en]:
                model.append([port])
            self.portCombo.set_active(0)
     
    def stream_changed_cb(self,combobox):
        proto=self.get_active_text(combobox)
        ipBox=self.builder.get_object('addressBox')
        if proto=='rtp':
            ipBox.set_text('@')
            ipBox.set_sensitive(False)
            return
        ipBox.set_sensitive(True)
        
    def dvb_changed_cb(self,combobox):
        self.playingChannel=self.get_active_text(combobox)
        self.builder.get_object('dvbButton').set_active(True)
        self.builder.get_object('title').set_text(self.playingChannel)
        
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0] 
           
    def port_changed_cb(self,entry):
        print entry.get_text()        
        
    def on_ui_destroy(self,widget):
        self.ui.destroy()
        
    def on_saveButton_clicked(self,widget):
        ip=self.ipCombo.child.get_text()
        port=self.portCombo.child.get_text()
        if validateIp(ip) and validatePort(port):
            if not self.servers.has_key(ip) or not port in self.servers[ip]:
                if not self.servers.has_key(ip):
                    self.servers[ip]=[port]
                    model=self.ipCombo.get_model()
                    model.append([ip])
                else:
                    self.servers[ip].append(port)
                self.parent.preferences.addServer(ip,port)
            else:
                print 'not saving'
        else:
            print 'not valid'
            
    def on_browse_button_clicked(self,widget,data=None):
        if self.parent.remote:
            self.browseRemote()
        else:
            self.browseLocal()
            
    def browseRemote(self):
        RemoteFileChooser(self.browseFinished,self.parent.interface)
            
    def browseLocal(self):
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
            #print dialog.get_filename(), 'selected'
            filename = dialog.get_filename()           
        elif response == gtk.RESPONSE_CANCEL:
            filename=None
            print 'Closed, no files selected'
        self.browseFinished(filename)
        dialog.destroy()
    
    def browseFinished(self,filename=None):
        if filename:
            self.builder.get_object("file_entry").set_text(filename)
            self.builder.get_object('fileButton').set_active(True)
            name=os.path.basename(filename)
            #name=name.split('.')
            #n=''.join(name[:-1],'.')
            n=name.rfind('.')
            self.builder.get_object('title').set_text(name[:n])
            
            
        
    def on_webcam_clicked(self,widget,data=None):
        if widget.get_active():
            self.source = 'webcam'
            

    def on_file_clicked(self,widget,data=None):
        if widget.get_active():
            self.source = 'file'
           

    def on_stream_clicked(self,widget,data=None):
        if widget.get_active():
            self.source = 'stream'
            
    def on_dvbButton_toggled(self,widget,data=None):
        if widget.get_active():
            self.source='tv'
            
    def on_settingsButton_clicked(self,widget):
        SettingsGui(self,True)
            
    def setSettings(self,settings):
        self.gotSettings=True
        self.settings=settings

    def on_defaultButton_clicked(self,widget):
        ip=self.ipCombo.child.get_text()
        if validateIp(ip):
            self.parent.preferences.setDefaultServer(ip)
        
    def on_registerButton_clicked(self,widget):
        if not self.gotSettings:
            s=SettingsGui(self,False)
            self.settings=s.getSettings()
            if not self.settings:
                SettingsGui(self,True)
                return
        
        self.settings['input']['advanced']=self.advSettings    
        if self.advSettings and self.source=='file' and self.advSettings['converted']:
            self.source='cfile'
   
        self.settings['type']=self.source
        self.settings['author']=self.builder.get_object('author').get_text()
        self.settings['title']=self.builder.get_object('title').get_text()
        self.settings['description']=self.builder.get_object('description').get_text()
        self.settings['filename']=None
        if 'file' in self.source:
            self.settings['filename']=self.builder.get_object('file_entry').get_text()
            if not self.settings['filename']:
                return
        if 'tv' in self.source:
            self.settings['filename']=(self.channels[self.playingChannel]['location'],self.channels[self.playingChannel]['program'])
        elif self.source=='stream':
            self.settings['filename']=self.get_active_text(self.streamCombo)+'://'+self.builder.get_object('addressBox').get_text()+':'+self.builder.get_object('port_entry').get_text()
            if not self.builder.get_object('addressBox').get_text():
                return
        self.settings['server']=(self.ipCombo.child.get_text(),self.portCombo.child.get_text())

        self.ui.destroy()
        
        
        if self.source=='file' and self.advSettings and self.advSettings['offline']:
            ConverterGui(self.parent,self.settings)
        else:        
            self.parent.registerStreamSettings(self.settings)


    def on_advancedButton_toggled(self,widget):
        if widget.get_active():
            FileGui(self)
            
    def setAdvancedSettings(self,advSettings):
        self.builder.get_object('advancedButton').set_active(False)
        if advSettings:
            self.advSettings=advSettings
            self.builder.get_object('browse_button').set_sensitive(False)
            self.browseFinished(self.advSettings['filename'])
            