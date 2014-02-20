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
from helper import validateIp,validatePort
from pkg_resources import resource_string


class AddServerGui(object):
    
    def __init__(self,func,ip=None,port=None,valid=False,args=None):
        self.func=func
        self.args=args
        self.destroy=False
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'addServer.glade'))
        self.builder.connect_signals(self)

        self.okButton=self.builder.get_object('okButton')
        
        self.ipEntry=self.builder.get_object('ipEntry')
        if ip:
            self.ipEntry.set_text(ip)
        else:
            self.ipEntry.grab_focus()
            
        self.portEntry=self.builder.get_object('portEntry')
        if port:
            self.portEntry.set_text(str(port))
        self.validCheck=self.builder.get_object('validButton')
        self.validCheck.set_active(valid)
            
        
    
        self.statusbar = self.builder.get_object("statusbar")
        self.context_id = self.statusbar.get_context_id("Statusbar")
        
        self.ui=self.builder.get_object('ui')
        self.ui.show()
    
    def on_okButton_clicked(self,widget):
        ip=self.ipEntry.get_text()
        if not validateIp(ip):
            m='enter valid ip'
            self.pushStatusBar(m)
            return
        port=self.portEntry.get_text()
        if not validatePort(port):
            m='enter valid port'
            self.pushStatusBar(m)
            return
        port=int(port)
        valid=self.validCheck.get_active()
        self.func(res=(ip,port,valid),args=self.args)
        self.destroy=True
        self.ui.destroy()
        
    def on_canclelButton_clicked(self,widget):
        self.ui.destroy()
    
    def on_ui_destroy(self,widget=None,data=None):
       if not self.destroy:
           self.func(res=None)
        
    def on_ipEntry_activate(self,*args):
        self.portEntry.grab_focus()
    
    def on_portEntry_activate(self,*args):
        self.validCheck.grab_focus()
        
    def on_validButton_toggled(self,*args):
        self.okButton.grab_focus()
        
    def pushStatusBar(self,data):
        self.statusbar.push(self.context_id, data)
        return
    
