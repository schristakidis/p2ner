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
from components import componentsFrame
from view import viewFrame
from optServers import serversFrame
from generic import genericFrame
from general import generalFrame
from optUpnp import upnpFrame
from dvbFrame import dvbFrame
from remoteproducer import remoteproducerFrame
from statistics import statisticsFrame
from subOpt import *
from subStats import *
from p2ner.abstract.ui import UI
from p2ner.util.utilities import compareIP,getIP
from pkg_resources import resource_string


class optionsGui(UI):
    def initUI(self):
    
        self.lastSelected=None
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'options.glade'))
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
        parent=optionsModel.append(None,['Statistics'])
        for stat in self.preferences.statsPrefs.keys():
            optionsModel.append(parent,[stat])
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
        
        self.mainBox=self.builder.get_object('vbox4')
        
        self.frames={}
        self.boxes={}
        self.makeFrames()
        
        
    def makeFrames(self):
        optionsModel=self.optionsModel
        piter = optionsModel.get_iter_first()
        while True:
            try:
                path = optionsModel.get_path(piter)
            except:
                break
            
            try:
                box=self.builder.get_object((optionsModel[path][0].lower()+'Frame'))
                box.set_visible(False)
            except:
                box=gtk.HBox()
                self.mainBox.pack_end(box,True,True)
                box.set_visible(False)
                
            self.boxes[optionsModel[path][0].lower()]=box
            
            frame=eval(optionsModel[path][0].lower()+'Frame(_parent=self)')

            self.frames[optionsModel[path][0]]=frame
            
            self.boxes[optionsModel[path][0].lower()].pack_start(frame.getFrame(),True,True,0)
            
            iter = optionsModel.iter_children(piter)
            while True:
                try:
                   path = optionsModel.get_path(iter)
                except:
                    break                
                try:
                    box=self.builder.get_object((optionsModel[path][0].lower()+'Frame'))
                    box.set_visible(False)
                except:
                    box=gtk.HBox()
                    self.mainBox.pack_end(box,True,True)
                    box.set_visible(False)
               
                self.boxes[optionsModel[path][0].lower()]=box
                    
                #try:
                frame=eval(optionsModel[path][0].lower()+'Frame(_parent=self)')
                #except:
                 #   print 'failed to load in option gui:',optionsModel[path][0].lower()
                 #   frame=genericFrame(_parent=self)    
                    
               
                self.boxes[optionsModel[path][0].lower()].pack_start(frame.getFrame(),True,True,0)
                
                self.frames[optionsModel[path][0]]=frame
                iter=optionsModel.iter_next(iter)
            piter=optionsModel.iter_next(piter)
      
    
    def showUI(self):
        for v in self.frames.values():
            v.refresh()
        self.ui.show()
        
            
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
                self.boxes[self.lastSelected.lower()].set_visible(False)
            self.lastSelected=opt
            self.builder.get_object('descLabel').set_text(opt)
            self.boxes[opt.lower()].set_visible(True)
            self.frames[opt].refresh()
    
        
    def on_saveButton_clicked(self,widget):
        self.preferences.save()
        
        
    def on_setDeafualtButton_clicked(self,widget):
        for v in self.frames.values():
            v.setDefaults()
        self.preferences.save()
        

        
    def on_okButton_clicked(self,widget):
        self.ui.hide()
            
    def loadColumnViews(self):
        if 'View' not in self.frames.keys():
            reactor.callLater(0.2,self.loadColumnViews)
            return
        self.frames['View'].loadViews()


    def getTable(self,component,sub,bar,id):
        return self.frames[component].constructPage(sub,bar,id)
    
    
    
        
if __name__=='__main__':
    s=optionsGUI()
    s.showUI()
    reactor.run()