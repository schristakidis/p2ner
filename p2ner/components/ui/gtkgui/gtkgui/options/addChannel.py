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
from pkg_resources import resource_string


class AddChannelGui(object):
    
    def __init__(self,func,name=None,location=None,prog=None,args=None):
        self.func=func
        self.args=args
        self.destroy=False
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'addChannel.glade'))
        self.builder.connect_signals(self)

        self.okButton=self.builder.get_object('okButton')
        
        self.nameEntry=self.builder.get_object('nameEntry')
        if name:
            self.nameEntry.set_text(name)
        else:
            self.nameEntry.grab_focus()
            
        self.locationEntry=self.builder.get_object('locationEntry')
        if location:
            self.locationEntry.set_text(location)
        
        self.progEntry=self.builder.get_object('programEntry')
        if prog:
            self.progEntry.set_text(str(prog))
        
        self.statusbar = self.builder.get_object("statusbar")
        self.context_id = self.statusbar.get_context_id("Statusbar")
        
        self.ui=self.builder.get_object('ui')
        self.ui.show()
    
    def on_okButton_clicked(self,widget):
        name=self.nameEntry.get_text()
        if not name:
            m='enter valid name'
            self.pushStatusBar(m)
            return
        loc=self.locationEntry.get_text()
        if not loc:
            m='enter valid location'
            self.pushStatusBar(m)
            return
        prog=self.progEntry.get_text()
        try:
            prog=int(prog)
        except:
            m='enter valid program number'
            self.pushStatusBar(m)
            return
        self.func(res=(name,loc,prog),args=self.args)
        self.destroy=True
        self.ui.destroy()
        
    def on_canclelButton_clicked(self,widget):
        self.ui.destroy()
    
    def on_ui_destroy(self,widget=None,data=None):
       if not self.destroy:
           self.func(res=None)
        
    def on_nameEntry_activate(self,*args):
        self.locationEntry.grab_focus()
    
    def on_locationEntry_activate(self,*args):
        self.progEntry.grab_focus()
        
    def on_programEntry_activate(self,*args):
        self.okButton.grab_focus()
        
    def pushStatusBar(self,data):
        self.statusbar.push(self.context_id, data)
        return
    