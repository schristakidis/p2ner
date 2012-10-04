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
from helper import validateIp,validatePort

class serversGUI(object):
    
    def __init__(self,parent):
    
        self.dirty=False
        self.parent=parent
    
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'serversGui.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'serversGui.glade'))
        
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
        self.dirty=True
        return
      
    def on_ok_clicked(self,widget):
        model=self.serversTreeview.get_model()
        serv=[]
        allserv=[]
        for s in model:
            if s[2]:
                serv.append((s[0],s[1]))
            allserv.append((s[0],s[1],bool(s[2])))
        self.ui.destroy()
        if self.dirty:
            self.parent.preferences.serversChanged(allserv)
        self.parent.setServers(serv)
    
    def loadServers(self):
        model=self.serversTreeview.get_model() 
        model.clear()
        servers=self.parent.preferences.getServers()
        for s in servers:
            model.append((s[0],s[1],s[2]))
        
    def on_ui_destroy(self,widget,data=None):
        #reactor.stop()
        pass

    
    def on_delete_clicked(self,widget):
        try:
            treeselection=self.serversTreeview.get_selection()
            (model, iter) = treeselection.get_selected()
            model.remove(iter)
            self.dirty=True
        except:
            self.pushStatusBar('you must select something first')
        
    def on_add_clicked(self,widget):
        AddServerGui(self)
    
    def newServer(self,ip,port,valid):
        model=self.serversTreeview.get_model()
        for server in model:
            if server[0]==ip and server[1]==port:
                self.pushStatusBar('server already in the list')
                return
        model.append((ip,port,valid))
        self.dirty=True
        
    def pushStatusBar(self,data):
        self.statusbar.push(self.context_id, data)
        return
    
    
class AddServerGui(object):
    
    def __init__(self,parent):
        self.parent=parent
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'addServer.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'addServer.glade'))
            
        self.builder.connect_signals(self)
        
        self.serversTreeview = self.builder.get_object("addServerView")
        model=self.serversTreeview.get_model()
        model.append(('',0,False))
    
        renderer=gtk.CellRendererText()
        renderer.set_property( 'editable', True )
        renderer.set_property('width',200)
        renderer.connect( 'edited', self.col0_edited_cb, model )
        column=gtk.TreeViewColumn("ip",renderer, text=0)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)

        renderer=gtk.CellRendererText()
        renderer.set_property( 'editable', True )
        renderer.set_property('width',50)
        renderer.connect( 'edited', self.col1_edited_cb, model )
        column=gtk.TreeViewColumn("port",renderer, text=1)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)

        renderer=gtk.CellRendererToggle()
        renderer.set_property('width',2)
        column=gtk.TreeViewColumn("valid",renderer, active=2)
        renderer.connect("toggled", self.toggled_cb, model)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)
        
        self.serversTreeview.show()
            
        self.statusbar = self.builder.get_object("statusbar")
        self.context_id = self.statusbar.get_context_id("Statusbar")
            
        self.ui = self.builder.get_object("ui")
        self.ui.show()
            
        
    def col0_edited_cb( self, cell, path, new_text, model ):
        if validateIp(new_text):
            model[path][0]=new_text
        else:
            self.pushStatusBar('not valid ip address')
    
        
    def col1_edited_cb( self, cell, path, new_text, model ):
        if validatePort(new_text):
            model[path][1]=int(new_text)
        else:
            self.pushStatusBar('not valid port')
            
    def toggled_cb(self,cell, path, user_data):
        model = user_data
        model[path][2] = not model[path][2]
        return      
        
    def pushStatusBar(self,data):
        self.statusbar.push(self.context_id, data)
        return
        

    
    def on_cancel_clicked(self,widget):
        self.ui.destroy()
        
    def on_ok_clicked(self,widget):
        model=self.serversTreeview.get_model()
        ip,port,valid=model.get(model.get_iter_first(),0,1,2) 
        if validateIp(ip) and validatePort(port):
            self.parent.newServer(ip,port,valid)
            self.ui.destroy()
        else:
            self.pushStatusBar('give a valid server')

if __name__=='__main__':

    serversGUI(None)
    reactor.run()
