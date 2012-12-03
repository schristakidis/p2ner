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
from p2ner.abstract.ui import UI
from options.addServer import AddServerGui

class serversGUI(UI):
    
    def initUI(self,parent):
        self.parent=parent
        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'serversGui.glade'))
        self.builder.connect_signals(self)

        self.serversTreeview = self.builder.get_object("serversTreeview")
        model=self.serversTreeview.get_model()

        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("ip",renderer, text=0)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)

        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("port",renderer, text=1)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)

        renderer=gtk.CellRendererToggle()
        column=gtk.TreeViewColumn("valid",renderer, active=2)
        renderer.connect("toggled", self.toggled_cb, model)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)
   
        self.serversTreeview.show()
        
        self.statusbar = self.builder.get_object("statusbar")
        self.context_id = self.statusbar.get_context_id("Statusbar")
    
        self.ui = self.builder.get_object("ui")
        self.ui.show()
    
        self.loadServers()
    
    
    def toggled_cb(self,cell, path, user_data):
        model = user_data
        model[path][2] = not model[path][2]
        self.preferences.setActiveServer(model[path][0],model[path][1],model[path][2])
        return
      
    def on_ok_clicked(self,widget):
        model=self.serversTreeview.get_model()
        serv=[(s[0],s[1]) for s in model if s[2]]
        self.ui.destroy()
        self.parent.setServers(serv)
    
    def loadServers(self):
        model=self.serversTreeview.get_model() 
        model.clear()
        servers=self.preferences.getServers()
        for s in servers:
            model.append((s[0],s[1],s[2]))
        
    def on_ui_destroy(self,widget,data=None):
        #reactor.stop()
        pass

    
    def on_delete_clicked(self,widget):
        try:
            treeselection=self.serversTreeview.get_selection()
            (model, iter) = treeselection.get_selected()
            ip=model.get_value(iter,0)
            port=model.get_value(iter,1)
            self.preferences.removeServer(ip,port)
            model.remove(iter)
        except:
            self.pushStatusBar('you must select something first')
        
    def on_add_clicked(self,widget):
        AddServerGui(self.newServer)
        
    def newServer(self,res,args=None):
        ip=res[0]
        port=res[1]
        valid=res[2]
        model=self.serversTreeview.get_model()
        for server in model:
            if server[0]==ip and server[1]==port:
                self.pushStatusBar('server already in the list')
                return
        model.append((ip,port,valid))
        self.preferences.addServer(ip,port,valid)
        
    def pushStatusBar(self,data):
        self.statusbar.push(self.context_id, data)
        return
    
 

if __name__=='__main__':

    serversGUI(None)
    reactor.run()
