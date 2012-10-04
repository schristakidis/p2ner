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
import p2ner.util.config as config
from p2ner.core.components import getComponentsInterfaces
from components import componentsFrame
from view import viewFrame
from optServers import serversFrame
from generic import genericFrame
from general import generalFrame
from optUpnp import upnpFrame
from dvbFrame import dvbFrame
from remoteproducer import remoteproducerFrame
from subOpt import *
from p2ner.abstract.ui import UI
from p2ner.util.utilities import compareIP,getIP



class optionsGui(UI):
    def initUI(self):#,parent,visibleCollumns):
    
        self.parent=self.root
        #self.visibleCollumns=visibleCollumns
        
        self.lastSelected=None
        
        if not self.remote:
            config.check_config()
            self.makeUI()
        else:
            self.copyConfig()
        
    def makeUI(self):
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'options.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'options.glade'))
        
        self.builder.connect_signals(self)
        
        optionsModel=gtk.TreeStore(str)
        self.optionsView=self.builder.get_object('optionsView')
        self.optionsView.set_model(optionsModel)
        
        optionsModel.append(None,['General'])
        optionsModel.append(None,['View'])
        optionsModel.append(None,['Servers'])
        parent=optionsModel.append(None,['Components'])
        optionsModel.append(parent,['Input'])
        optionsModel.append(parent,['Output'])
        optionsModel.append(parent,['Scheduler'])
        optionsModel.append(parent,['Overlay'])
        optionsModel.append(None,['UPNP'])
        optionsModel.append(None,['DVB'])
        optionsModel.append(None,['RemoteProducer'])
               
        renderer=gtk.CellRendererText()   
        column=gtk.TreeViewColumn('Options',renderer, text=0)
        column.set_resizable(True)
        column.set_visible(True)
        self.optionsView.append_column(column)
            
        self.optionsView.show()
        self.ui=self.builder.get_object('ui')
        self.ui.set_title('Preferences')
        
        self.optionsModel=optionsModel  
        self.getComponents()
        
        
        self.frames={}

        
        
    def makeFrames(self):
        optionsModel=self.optionsModel
        piter = optionsModel.get_iter_first()
        while True:
            try:
                path = optionsModel.get_path(piter)
            except:
                break
            self.builder.get_object((optionsModel[path][0].lower()+'Frame')).set_visible(False)
            #try:
            frame=eval(optionsModel[path][0].lower()+'Frame(self)')
            #except:
             #   print optionsModel[path][0].lower()
              #  frame=genericFrame()    
            
            #if optionsModel[path][0].lower()=='dvb':
            #   frame=generalFrame(self)    
            self.frames[optionsModel[path][0]]=frame
            
            self.builder.get_object((optionsModel[path][0].lower()+'Frame')).pack_start(frame.getFrame(),True,True,0)
            iter = optionsModel.iter_children(piter)
            while True:
                try:
                   path = optionsModel.get_path(iter)
                except:
                    break                
                self.builder.get_object((optionsModel[path][0].lower()+'Frame')).set_visible(False)
                try:
                    frame=eval(optionsModel[path][0].lower()+'Frame(self)')
                except:
                    print optionsModel[path][0].lower()
                    frame=genericFrame()    
                    
               
                self.builder.get_object((optionsModel[path][0].lower()+'Frame')).pack_start(frame.getFrame(),True,True,0)
                
                self.frames[optionsModel[path][0]]=frame
                iter=optionsModel.iter_next(iter)
            piter=optionsModel.iter_next(piter)
      
    
    def showUI(self):
        for v in self.frames.values():
            v.refresh()
        self.ui.show()
        
    def getComponents(self):
        self.components={}
        for comp in ['input','output','scheduler','overlay']:
            reactor.callLater(0,self.interface.getComponentsInterfaces,comp)
            #self.interface.getComponentsInterfaces(comp)
            #self.components[comp]=getComponentsInterfaces(comp)
      
    def setComponent(self,comp,interface):
        self.components[comp]=interface
        for c in ['input','output','scheduler','overlay']:
            if c not in self.components.keys():
                return
        self.makeFrames()
        self.parent.continueUI()
            
    def on_optionsView_cursor_changed(self,widget):
        treeselection=self.optionsView.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path = model.get_path(iter)
        except:
            path=(0,)
        
        opt=model[path][0]
        if opt!=self.lastSelected:
            if self.lastSelected:
                self.builder.get_object((self.lastSelected.lower()+'Frame')).set_visible(False)
            self.lastSelected=opt
            self.builder.get_object('descLabel').set_text(opt)
            self.builder.get_object((opt.lower()+'Frame')).set_visible(True)
            self.frames[opt].refresh()
    
        
    def on_saveButton_clicked(self,widget):
        for v in self.frames.values():
            v.save()
        config.save_config()
        
    def on_setDeafualtButton_clicked(self,widget):
        for v in self.frames.values():
            v.setDefaults()
        config.save_config()
        

        
    def on_okButton_clicked(self,widget):
        self.ui.hide()
            
    def loadColumnViews(self):
        if 'View' not in self.frames.keys():
            reactor.callLater(0.2,self.loadColumnViews)
            return
        self.frames['View'].loadViews()
        
    def getActiveServers(self):
        return self.frames['Servers'].getActiveServers()
    
    def getServers(self):
        return self.frames['Servers'].getServers()
    
    def serversChanged(self,servers):
        self.frames['Servers'].serversChanged(servers)
    
    def getDefaultServer(self):
        return self.frames['Servers'].getDefaultServer()

    def setDefaultServer(self,ip):
        self.frames['Servers'].setDefaultServer(ip)
        
    def addServer(self,ip,port):
        self.frames['Servers'].addServer(ip,port)
        
    def getCheckNetAtStart(self):
        if 'General' not in self.frames.keys():
            reactor.callLater(0.2,self.getCheckNetAtStart)
        else:
            return self.frames['General'].getCheckNetAtStart()
    
    def setCheckNetAtStart(self,check):
        self.frames['General'].setCheckNetAtStart(check)
        
    def getCheckAtStart(self):
        if 'General' not in self.frames.keys():
            reactor.callLater(0.2,self.getCheckAtStart)
        else:
            return self.frames['General'].getCheckAtStart()
    
    def getAllComponents(self,component):
        return self.frames['Components'].getComponents(component)
    
    def getTable(self,component,sub,bar,id):
        return self.frames[component].constructPage(sub,bar,id)
    
    def getSettings(self,component):
        return self.frames[component].getSettings()
    
    def updateSettings(self,component,settings):
        self.frames[component].updateSettings(settings)
        
    def saveSettings(self):
        for v in self.frames.values():
            v.save()
        config.save_config()
        
    def getCdir(self):
        return self.frames['General'].getCdir()
        
    def getSubEncodings(self):
        return self.frames['General'].getSubEncodings()
    
    def getChannels(self):
        return self.frames['DVB'].getChannels()
    
    def copyConfig(self):
        reactor.callLater(0,self.interface.copyConfig)
        
    def getConfig(self,file):
        config.create_remote_config(file[0],file[1],True)
        self.makeUI()
        
    def saveRemoteConfig(self):
        filename=config.check_config()
        f=open(filename,'rb')
        b=f.readlines()
        f.close()
        filename=config.check_chConfig()
        f=open(filename,'rb')
        r=f.readlines()
        f.close()
        self.interface.sendRemoteConfig(b,r)
        
    
    def writeBW(self,bw):
        config.writeBW(bw,self.parent.extIP)
        
if __name__=='__main__':
    s=optionsGUI()
    s.showUI()
    reactor.run()