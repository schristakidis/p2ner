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
from p2ner.base.Peer import Peer
from pkg_resources import resource_string

class ChatClient(object):
    def __init__(self,parent):
        self.parent=parent
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        
        """
        try:
            self.builder.add_from_file(os.path.join(path,'chatgui.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'chatgui.glade'))
        """
        
        self.builder.add_from_string(resource_string(__name__, 'chatgui.glade'))
        self.builder.connect_signals(self)
        
        roomsModel=gtk.ListStore(int)
        self.roomsView=self.builder.get_object('roomsView')
        self.roomsView.set_model(roomsModel)
        
        renderer=gtk.CellRendererText()   
        column=gtk.TreeViewColumn('Rooms',renderer, text=0)
        column.set_visible(True)
        self.roomsView.append_column(column)
        self.roomsView.set_headers_visible(False)
        self.roomsView.show()
        
        usersModel=gtk.ListStore(str,str,int)
        self.usersView=self.builder.get_object('usersView')
        self.usersView.set_model(usersModel)
        
        renderer=gtk.CellRendererText()   
        column=gtk.TreeViewColumn('Users',renderer, text=0)
        column.set_visible(True)
        self.usersView.append_column(column)
        
        self.usersView.show()
        
        self.mainView=self.builder.get_object('mainview')    
        self.mainView.set_buffer(gtk.TextBuffer())
        
        self.userView=self.builder.get_object('messageView')    
        
        self.userView.connect('key-press-event', self.keyPress)
        
        self.mainBox=self.builder.get_object('mainBox')
        self.userBox=self.builder.get_object('userBox')
        self.mainBox.set_sensitive(False)
        
        self.ui=self.builder.get_object('ui')
        self.ui.show()
        
        self.username=None
        self.regid=None

    def show(self):
        self.ui.show()
        
    def getStreams(self):
        ids=self.parent.getStreamsIds()
        self.avids={}
        for id in ids:
            self.avids[id[0]]=Peer(id[1],id[2])

        model=self.roomsView.get_model()
        for id in self.avids.keys():
            model.append([id])
        
        if not self.regid and len(ids)==1:
            self.registerChat(model[0][0])
        else:
            mes='*choose a  chat room from the list in the left \n'
            self.addText(mes, self.mainView)
        
    def on_roomvie_row_activated(self,widget,path,col):
        model=widget.get_model()
        id=model[path][0]
        if id!=self.regid:
            self.registerChat(id)
        
    def registerChat(self,id):
        if self.regid and self.regid!=id:
            self.unregisterChat(self.regid,self.regserver)
            
        if self.regid!=id:
            self.regid=id
            self.regserver=self.avids[int(id)]
            self.parent.interface.joinChatRoom(id,self.username,self.regserver)
            #self.userView.set_buffer(gtk.TextBuffer())
            m=self.usersView.get_model()
            m.clear()
            m.append([self.username,'',0])
            self.mainView.set_buffer(gtk.TextBuffer())
            mes='*joined chat room:'+str(id)+'\n'
            self.addText(mes, self.mainView)
        
    def newChatter(self,id,username,new):
        if id!=self.regid:
            print 'got chat message for a non register id'
            return
        if new:
            for u in username:
                self.usersView.get_model().append([u[0],u[1],u[2]])
                mes='*'+str(u[0])+' joined the room\n'
                self.addText(mes,self.mainView)
        else:
            for u in username:
                treeiter =self.usersView.get_model().get_iter_first()
                for m in self.usersView.get_model():
                    if u[1]==m[1] and u[2]==m[2]:
                        self.usersView.get_model().remove(treeiter)
                        mes='*'+str(u[0])+' has left the room\n'
                        self.addText(mes,self.mainView)
                        break
                    treeiter = self.usersView.get_model().iter_next(treeiter)

    def newChatMessage(self,id,message,peer):
        model=self.usersView.get_model()
        for m in model:
            if m[1]==peer[0] and m[2]==peer[1]:
                mes= message.strip()+'\n'
                self.addText(mes,self.mainView)
                break

                
    def keyPress(self,widget,event):
        if event.keyval == 65293:
            buf=self.userView.get_buffer()
            mes=buf.get_text(buf.get_start_iter(),buf.get_end_iter())
            buf.delete(buf.get_start_iter(),buf.get_end_iter())
            mes = self.username+':'+mes.strip() +'\n'           
            self.addText(mes, self.mainView)
            self.parent.interface.sendChatMessage(self.regid,mes,self.regserver)
            
    def addText(self,mes,view):
        text=mes
        buf=view.get_buffer()
        buf.insert(buf.get_end_iter(),text)
        view.scroll_to_mark(buf.get_insert(),0)
        
    def on_nameEntry_activate(self,widget):
        self.username=self.builder.get_object('nameEntry').get_text()
        if self.username:
            self.userBox.set_visible(False)
            self.mainBox.set_sensitive(True)
            self.getStreams()
            
    def on_ui_destroy(self,*args):
        if self.regid:
            self.unregisterChat(self.regid,self.regserver)
            self.regid=None
        self.parent.chatClientUI=None
            
    def unregisterChat(self,id,server):
         self.parent.interface.leaveChatRoom(id,self.username,server)
 
