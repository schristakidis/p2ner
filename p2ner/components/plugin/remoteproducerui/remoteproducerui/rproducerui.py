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
from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from cPickle import loads,dumps
from twisted.web.xmlrpc import Proxy
from p2ner.abstract.ui import UI
from connectgui import ConnectGui
from twisted.web.xmlrpc import Proxy
from gtkgui.settings import SettingsGui
import getpass

class RemoteProducerUI(UI):
    def initUI(self):
        ConnectGui(self)
        self.ui=None
        self.gotSettings=False
        self.proxy=None
        
    def constructUI(self):
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'viewer.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'viewer.glade'))
            
        self.ui=self.builder.get_object('ui')
        
        self.builder.connect_signals(self)
        
        self.model = gtk.TreeStore(gobject.TYPE_STRING)#,gobject.TYPE_BOOLEAN )
        
        self.tVideo=self.model.append(None,('Videos',))
        #self.model.append(self.tVideo,('Videos333333',))
        self.tChannel=self.model.append(None,('Channels',))        
        #self.model.append(self.tChannel,('Videos332222',))
        
        self.treeview=self.builder.get_object('treeview')
        self.treeview.set_model(self.model)
        self.treeview.set_headers_visible(False)
        
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('streams',renderer, text=0)
        self.treeview.append_column(column)
        
    def startUI(self):
        if not self.proxy:
            ConnectGui(self)
            return
        self.constructUI()
        self.getContents()
        self.ui.show()
        
    def setURL(self,url,ip):
        self.proxy = Proxy(url)
        self.server=ip
        
    def on_treeview_row_activated(self,widget,path,col):
        if len(path)==1:
            if self.treeview.row_expanded(path):
                self.treeview.collapse_row(path)
            else:
                self.treeview.expand_row(path,True)
        else:
            stream=self.model[path][0]
            if path[0]==0:
                type='file'
            else:
                type='tv'
            self.treeview.set_sensitive(False)
            self.registerStream(type,stream)
            
            
    def getContents(self):
        d=self.proxy.callRemote('getContents')
        d.addCallback(self.updateView)
        d.addErrback(self.XMLRPCFailed)
        
    def XMLRPCFailed(self,reason):
        print reason
        
    def updateView(self,contents):
        videos=contents[0]
        channels=contents[1]
        for v in videos:
            self.model.append(self.tVideo,(v,))
        for ch in channels:
            self.model.append(self.tChannel,(ch,))
            
    def on_closeButton_clicked(self,widget):
        self.ui.destroy()
        
    def on_settingsButton_clicked(self,widget):
        SettingsGui(self,True)
        
    def setSettings(self,settings):
        self.gotSettings=True
        self.settings=settings
        print self.settings
        
    def registerStream(self,type,stream):
        if not self.gotSettings:
            s=SettingsGui(self,False)
            self.settings=s.getSettings()
            if not self.settings:
                SettingsGui(self,True)
                return
        
        self.settings['input']['advanced']=False 
   
        self.settings['type']=type
        self.settings['author']=getpass.getuser()
        self.settings['title']=stream
        self.settings['description']=''
        self.settings['filename']=stream

        
        
        port=16000
        self.settings['server']=(self.server,port)

        #self.ui.destroy()
        input=self.settings.pop('input')
        output={}
        output['comp']='NullOutput'
        output['kwargs']=None
        
        d = self.proxy.callRemote('registerStream', dumps(self.settings),dumps(input),dumps(output))
        d.addCallback(self.subscribeStream,self.server,port)
        d.addErrback(self.XMLRPCFailed)
        
    def subscribeStream(self,id,ip,port):
        if id==-1:
            print 'waittttttttttt'
        elif id==-2:
            print 'failed to register stream'
            self.treeview.set_sensitive(True)
        else:
            self.parent.on_refreshButton_clicked()
            reactor.callLater(2,self.parent.subscribeStream,id,ip,port,True)
            reactor.callLater(2.5,self.treeview.set_sensitive,True)
        
            