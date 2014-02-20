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
from helper import validateIp
from pkg_resources import resource_string

class MeasureUpload(object):
    def __init__(self,parent):
        self.parent=parent
        
        self.builder = gtk.Builder()
        """
        try:
            self.builder.add_from_file(os.path.join(path,'measureupload.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'measureupload.glade'))
        """
        self.builder.add_from_string(resource_string(__name__, 'measureupload.glade'))
        self.builder.connect_signals(self)

        self.servers=self.getServers()
        
        servListstore=gtk.ListStore(str)

        for s in self.servers.keys():
            servListstore.append([s])   
        
        
        self.ipCombo = gtk.ComboBoxEntry(servListstore, 0)

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
            
        self.tview=self.builder.get_object('textview')    
        self.tbuffer=gtk.TextBuffer()
        self.tview.set_buffer(self.tbuffer)
        
        self.addText('Choose server and press Start')

        self.ui=self.builder.get_object('ui')
        self.ui.show()
        
    def addText(self,text):
        text +='\n'
        self.tbuffer.insert(self.tbuffer.get_end_iter(),text)
    
    def getServers(self):
        srv=self.parent.preferences.getServers()
        servers={}
        for s in srv:
            if not servers.has_key(s[0]):
                servers[s[0]]=[]
            servers[s[0]].append(s[1])
        return servers
    
    def get_active_text(self,combobox):
        return combobox.get_child().get_text()
        
    def on_closeButton_clicked(self,widget):
        self.ui.destroy()
        
    def on_saveButton_clicked(self,widget):
        ip=self.ipCombo.child.get_text()
        if validateIp(ip):
            if not self.servers.has_key(ip):
                    self.servers[ip]=[16000]
                    model=self.ipCombo.get_model()
                    model.append([ip])
                    self.parent.preferences.addServer(ip,16000)

    
    def on_defaultButton_clicked(self,widget):
        ip=self.ipCombo.child.get_text()
        if validateIp(ip):
            self.parent.preferences.setDefaultServer(ip)
            
    def on_startButton_clicked(self,widget):
        text=widget.get_label()
        if text=='Start':
            self.startMeasurement()
        else:
            self.setBW()
            
    def startMeasurement(self):
        ip=self.get_active_text(self.ipCombo)
        if not ip:
            text='The ip of the server is not valid'
            self.addText(text)
            return
        text='Contacting server '+ip
        self.addText(text)
        
        self.builder.get_object('startButton').set_sensitive(False)
        self.parent.interface.startBWMeasurement(ip,self)
        
    def connectionFailed(self):
        self.builder.get_object('startButton').set_sensitive(True)
        self.addText('Connection to the server failed')
        
    def getResults(self,bw):
        if bw==-1:
            self.connectionFailed()
            return
        
        text='Your measured upload bw is '+str(bw)+' KBytes/sec'
        self.addText(text)
        text='Do you want to set it as your sending rate?'
        self.addText(text)
        self.builder.get_object('startButton').set_label('Set BW')
        self.builder.get_object('startButton').set_sensitive(True)
        self.bw=bw
        
    def setBW(self):
        self.parent.interface.setBW(self.bw)
        self.parent.preferences.writeBW(self.bw)
        self.ui.destroy()
        
