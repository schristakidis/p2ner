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

import pygtk
from twisted.internet import reactor
pygtk.require("2.0")
import gtk
import gobject
from helper import validateIp,validatePort
from generic import genericFrame
from pkg_resources import resource_string
from addServer import AddServerGui

class serversFrame(genericFrame):
    
    def initUI(self):
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'optServers.glade'))
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
        renderer.set_property('xpad',5)
        column=gtk.TreeViewColumn("valid",renderer, active=2)
        renderer.connect("toggled", self.toggled_cb, model)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)
   
        self.serversTreeview.show()

        self.ui = self.builder.get_object("ui")
        self.ui.show()
        self.frame=self.ui
        self.loadServers()
        

    def refresh(self):
        self.loadServers()

        
    def toggled_cb(self,cell, path, user_data):
        model = user_data
        model[path][2] = not model[path][2]
        self.preferences.setActiveServer(model[path][0],model[path][1],model[path][2])
        return
      
    
    def loadServers(self):
        model=self.serversTreeview.get_model() 
        model.clear()
        servers=self.preferences.loadServers()
        for server in servers:
            model.append((str(server['ip']),int(server['port']),server['valid']))
        self.setDefaultServer()

    def setDefaultServer(self):
        default=self.preferences.getDefaultServer()
        if default:
            self.builder.get_object('defaultEntry').set_text(str(default))
        else:
            self.builder.get_object('defaultEntry').set_text('')
            
    def on_editButton_clicked(self,widget):
        treeselection=self.serversTreeview.get_selection()
        try:
            (model, iter) = treeselection.get_selected()
            path=model.get_path(iter)
        except:
            return
        self.serversTreeview.set_sensitive(False)
        AddServerGui(self.newServer,model.get_value(iter,0),model.get_value(iter,1),model.get_value(iter,2),iter)
        

                                          
    def on_deleteButton_clicked(self,widget):
        treeselection=self.serversTreeview.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path=model.get_path(iter)
        except:
            return
        
        self.preferences.removeServer(model.get_value(iter,0),model.get_value(iter,1))
        s=model[path][0]
        model.remove(iter)
        self.setDefaultServer()
            
    def on_newButton_clicked(self,widget):
        self.serversTreeview.set_sensitive(False)
        AddServerGui(self.newServer)
        return
            
    def newServer(self,res=None,args=None):
        self.serversTreeview.set_sensitive(True)
        if not res:
            return
        
        ip=res[0]
        port=res[1]
        valid=res[2]
       
        model=self.serversTreeview.get_model()
        if not args:
            if self.checkNewServer(ip,port):
                model.append((ip,port,valid))
                self.preferences.addServer(ip,port,valid)
        else:
            iter=args
            old=[]
            old.append(model.get_value(iter,0))
            model.set_value(iter,0,ip)
            old.append(model.get_value(iter,1))
            model.set_value(iter,1,port)
            old.append(model.get_value(iter,2))
            model.set_value(iter,2,valid)
            self.preferences.changeServer(old,(ip,port,valid))
            self.setDefaultServer()
                
    def checkNewServer(self,ip,port):
        model=self.serversTreeview.get_model()   
        m=[s for s in model if ip==s[0] and port==s[1]] 
        if len(m):
            return False
        else:
            return True
        
    def on_default_clicked(self,widget):
        treeselection=self.serversTreeview.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path=model.get_path(iter)
        except:
            return
        
        self.builder.get_object('defaultEntry').set_text(model[path][0])
        self.preferences.setDefaultServer(model[path][0])
        

  