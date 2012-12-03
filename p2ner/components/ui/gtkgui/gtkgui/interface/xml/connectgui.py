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

from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from twisted.web.xmlrpc import Proxy
from pkg_resources import resource_string

class ConnectGui(object):
    
    def __init__(self,parent):
        self.parent=parent
        
        self.builder=gtk.Builder()    
        self.builder.add_from_string(resource_string(__name__, 'connect.glade'))
      
        self.builder.connect_signals(self)
        
        self.statusbar = self.builder.get_object("statusbar")
        self.context_id = self.statusbar.get_context_id("Statusbar")
        
        self.ui = self.builder.get_object("ui")
        self.ui.show()
        
    def on_connectButton_clicked(self,widget):
        ip=self.builder.get_object('ipEntry').get_text()
        port=self.builder.get_object('portEntry').get_text()
        self.url="http://"+ip+':'+port+"/XMLRPC"
        print self.url
        proxy = Proxy(self.url)
        d =proxy.callRemote('connect')
        d.addCallback(self.succesfulConnection)
        d.addErrback(self.failedConnection)
        
    def succesfulConnection(self,d):
        self.parent.interface.setUrl(self.url)
        self.parent.loadPreferences()
        self.ui.destroy()
        
    def failedConnection(self,f):
        self.statusbar.push(self.context_id, "Can't connect to server")
        print f
        
    def on_exitButton_clicked(self,widget):
        self.ui.destroy()
        self.root.quit()
        reactor.stop()
