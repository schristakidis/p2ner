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
import p2ner.util.config as config
from helper import validateIp,validatePort
from generic import genericFrame

class serversFrame(genericFrame):
    
    def __init__(self,parent):

        self.parent=parent
        self.ipBack=('f',0)
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'optServers.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'optServers.glade'))
        
        self.builder.connect_signals(self)

        self.serversTreeview = self.builder.get_object("serversTreeview")
        model=self.serversTreeview.get_model()

        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("ip",renderer, text=0,editable=3)
        renderer.connect('edited', self.ip_edited_cb,0,model)
        renderer.connect('editing_canceled', self.ip_edited_canceled)
        column.set_resizable(True)
        self.serversTreeview.append_column(column)
        self.ipCol=column
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("port",renderer, text=1,editable=3)
        renderer.connect('edited', self.port_edited_cb,1,model)
        renderer.connect('editing_canceled', self.port_edited_canceled)
        column.set_resizable(True)
        self.portCol=column
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
    
    def ip_edited_cb(self,cell,path,text,col,model):
        self.ipBack=(model[path][col],path)
        if validateIp(text):
            model[path][col]=text
        else:
            model[path][3]=False
            if self.ipBack[0]=='':
                model.remove(model.get_iter(path))
            return
        
        self.serversTreeview.set_cursor(path,self.portCol,start_editing=True)
        p=self.serversTreeview.get_children()
        p[0].grab_focus()
        
    def ip_edited_canceled(self,*p):
        model=self.serversTreeview.get_model()
        if self.ipBack[0]=='':
            model.remove(model.get_iter(len(model)-1))
        for m in self.serversTreeview.get_model():
            m[3]=False
            
    def port_edited_canceled(self,*p):
        if int(self.serversTreeview.get_cursor()[0][0])==int(self.ipBack[1]):
            return
        model=self.serversTreeview.get_model()
        model[self.ipBack[1]][0]=self.ipBack[0]
        if self.ipBack[0]=='':
            model.remove(model.get_iter(len(model)-1))
        for m in model:
            m[3]=False

    def port_edited_cb(self,cell,path,text,col,model):
        if validatePort(text):
            model[path][col]=int(text)
            if self.ipBack[0]==self.builder.get_object('defaultEntry').get_text():
                self.builder.get_object('defaultEntry').set_text('')
        else:
            model[self.ipBack[1]][0]=self.ipBack[0]
            if self.ipBack[0]=='':
                model.remove(model.get_iter(path))
        model[path][3]=False
        
        
    def toggled_cb(self,cell, path, user_data):
        model = user_data
        model[path][2] = not model[path][2]
        return
      
    
    def loadServers(self):
        model=self.serversTreeview.get_model() 
        model.clear()
        servers=config.get_servers()
        for server in servers:
            button=gtk.Button()
            model.append((str(server['ip']),int(server['port']),server['valid'],False))
        
        try:
            default=config.config.get('DefaultServ','ip')
        except:
            default=None
            
        if default:
            self.builder.get_object('defaultEntry').set_text(str(default))

    def on_editButton_clicked(self,widget):
        treeselection=self.serversTreeview.get_selection()
        try:
            (model, iter) = treeselection.get_selected()
            path=model.get_path(iter)
        except:
            return
        model.set_value(iter,3,True)
     
        self.serversTreeview.set_cursor(path,self.ipCol,start_editing=True)
        p=self.serversTreeview.get_children()
        p[0].grab_focus()

                                          
    def on_deleteButton_clicked(self,widget):
        treeselection=self.serversTreeview.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path=model.get_path(iter)
        except:
            return
        s=model[path][0]
        model.remove(iter)
        if s==self.builder.get_object('defaultEntry').get_text():
            self.builder.get_object('defaultEntry').set_text('')
            
    def on_newButton_clicked(self,widget):
        model=self.serversTreeview.get_model()
        model.append(['',0,True,True])
        path=len(model)-1
        self.ipBack=('',0)
        self.serversTreeview.set_cursor(path,self.ipCol,start_editing=True)
        p=self.serversTreeview.get_children()
        p[0].grab_focus()
            
    def on_default_clicked(self,widget):
        treeselection=self.serversTreeview.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path=model.get_path(iter)
        except:
            return
        
        self.builder.get_object('defaultEntry').set_text(model[path][0])
        
    def getActiveServers(self):
        serv=[]
        for s in self.serversTreeview.get_model():
            if s[2]:
                serv.append((s[0],s[1]))
        return serv
    
    def getServers(self):
        serv=[]
        for s in self.serversTreeview.get_model():
            serv.append((s[0],s[1],s[2]))
        return serv
    
    def setDefaultServer(self,server):
        self.builder.get_object('defaultEntry').set_text(str(server))
        config.config.set('DefaultServ','ip',self.getDefaultServer())
        config.save_config()
        
    def getDefaultServer(self):
        return self.builder.get_object('defaultEntry').get_text()
    
    def save(self):
        config.config.set('DefaultServ','ip',self.getDefaultServer())
        config.writeChanges(self.getServers())
        config.save_config()
        
    def serversChanged(self,servers):
        model=self.serversTreeview.get_model()
        model.clear()
        dServ=self.getDefaultServer()
        found=False
        for s in servers:
            model.append((s[0],s[1],s[2],False))
            if s[0]==dServ:
                found=True
                
        if not found:
            self.setDefaultServer('')
            
        self.save()
        config.save_config()
    
    def addServer(self,ip,port):
        model=self.serversTreeview.get_model()
        found=False
        for m in model:
            if m[0]==ip and int(m[1])==int(port):
                found=True
        if not found:
            model.append([ip,int(port),True,False])
            config.writeChanges(self.getServers())
            config.save_config()
        