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

from gtkgui.producerGui import ProducerGui
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from gtkgui.interface.xml.xmlinterface import Interface
from p2ner.core.preferences import Preferences
from gtkgui.remotefilechooser import RemoteFileChooser
from twisted.internet import reactor
from proxyinterface import ProxyInterface

OFF=0
ON=1
INPROGRESS=2
PAUSE=3

class PGui(ProducerGui):
    def initUI(self,parent,peer):
        self.peer=peer
        self.parent=parent
        if self.proxy:
            self.interface=ProxyInterface(self,_parent=self)
            self.interface.setProxy(self.proxy)
            self.interface.setForwardPeer(peer)
        else:
            self.interface=Interface(_parent=self)
            url="http://"+peer[0]+':'+str(peer[1])+"/XMLRPC"
            self.interface.setUrl(url)
            
        self.preferences=Preferences(_parent=self,remote=True,func=self.continueUI)
        self.preferences.start()
        self.visibleCollumns=[]

        
    def continueUI(self):
        ProducerGui.initUI(self,self.parent)
        box=self.builder.get_object("NullBox")
        button = gtk.RadioButton(group=self.builder.get_object('webcamButton'),label='Random Input')
        button.connect('toggled',self.on_nullButton_clicked)
        button.show()
        button.set_active(True)
        box.pack_start(button,False,False)
        box.show()
        
        box=self.builder.get_object("NullEntryBox")
        self.nullEntry=gtk.Entry()
        self.nullEntry.show()
        box.pack_start(self.nullEntry,False,False)
        box.show()
        
    def on_nullButton_clicked(self,widget):
        if widget.get_active():
            self.source='RandomInput'

        
    def getServers(self):
        return self.parent.getServers()
    
    def getChannels(self):
        return {}

    def getDefaultServer(self):
        return 0

    def on_ui_destroy(self,widget=None):
        #self.preferences.saveRemoteConfig(False)    
        self.ui.destroy()
        

    def registerStreamSettings(self):
        input=self.settings.pop('input')
        output={}
        output['comp']='NullOutput'
        output['kwargs']=None
        self.parent.setStatus(self.peer,INPROGRESS)
        print self.settings
        if self.settings['type']=='RandomInput' and input['component']!='RandomInput':
            input['component']='RandomInput'
            videoRate=self.nullEntry.get_text()
            try:
                videoRate=int(videoRate)
            except:
                return
            input['videoRate']=videoRate
        self.on_ui_destroy()
        self.interface.registerStream(self.settings,input,output)
        
    def registerStream(self,streams):
        stream=streams[0]
        if stream==-1:
            self.parent.setStatus(self.peer,OFF)
        else:
            print stream
            self.parent.setStatus(self.peer,PAUSE)
            self.parent.setId(self.peer,stream.id)
            print stream.server[0],stream.server[1]
            self.parent.setId((stream.server[0],stream.server[1]),stream.id,True)
         