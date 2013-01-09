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
from pkg_resources import resource_string
from p2ner.abstract.ui import UI

class NetworkGui(UI):
    def initUI(self):

        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'networkGui.glade'))
        self.builder.connect_signals(self)
            
        self.tview=self.builder.get_object('textview')    
        self.tbuffer=gtk.TextBuffer()
        self.tview.set_buffer(self.tbuffer)
        
        self.addText('Checking network conditions...')

        self.ui=self.builder.get_object('ui')
        #self.ui.show()
        
    def show(self):
        self.ui.show()
        
    def addText(self,text):
        text +='\n'
        iter=self.tbuffer.get_end_iter()
        self.tbuffer.insert(iter,text)
        #self.tview.scroll_to_iter(iter,0)
        try:
            adj=self.builder.get_object('scrolledwindow1').get_vadjustment()
            adj.set_value(adj.upper)
        except:
            pass
       
        
    def on_closeButton_clicked(self,widget):
        self.preferences.setCheckNetAtStart(not self.builder.get_object('startUpButton').get_active(),save=True)
        self.ui.destroy()
        
    def on_startUpButton_toggled(self,widget):
        print 'on start :',widget.get_active()