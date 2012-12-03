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
from generic import genericFrame
from pkg_resources import resource_string

class viewFrame(genericFrame):
    def initUI(self):
        self.collumns=self.visibleCollumns

        self.builder = gtk.Builder()
        
        self.builder.add_from_string(resource_string(__name__, 'optView.glade'))
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('viewFrame')
        
        self.viewTree=self.builder.get_object('viewTree')
        self.hideTree=self.builder.get_object('hideTree')
        
        renderer=gtk.CellRendererText()   
        column=gtk.TreeViewColumn('Show',renderer, text=0)
        column.set_visible(True)
        self.viewTree.append_column(column)
        
        renderer=gtk.CellRendererText()   
        column=gtk.TreeViewColumn('Hide',renderer, text=0)
        column.set_visible(True)
        self.hideTree.append_column(column)
        
        self.colWig={}
        for c in self.collumns:
            self.colWig[c.get_name()]=c
            
        
    def getFrame(self):
        return self.frame
    
    def refresh(self):
        self.constructViews()
        
    def loadViews(self):
        self.constructViews(True)
        
    def constructViews(self,first=False):
        showModel=gtk.ListStore(str)
        hideModel=gtk.ListStore(str)

        self.viewTree.set_model(showModel)
        self.hideTree.set_model(hideModel)
        
        if first:
            for name,wig in self.colWig.items():
                active=self.preferences.getCollumnVisibility(name)
                wig.set_active(active)
                if active:
                    showModel.append([name])
                else:
                     hideModel.append([name])
            return
        
        for c in self.collumns:
            if c.get_active():
                showModel.append([c.get_name()])
            else:
                hideModel.append([c.get_name()])
        
        
    def on_hideTree_focus_in_event(self,widget,d):
        self.builder.get_object('showButton').set_label('Show')
    
    def on_viewTree_focus_in_event(self,widget,d):
        self.builder.get_object('showButton').set_label('Hide')
        
    def on_viewTree_row_activated(self,widget,path,col):
        model=widget.get_model()
        v=model[path][0]
        model.remove(model.get_iter(path))
        
        self.colWig[v].set_active(False)
        self.hideTree.get_model().append([v])
        self.preferences.changeVisibility(v,False)
        
    def on_hideTree_row_activated(self,widget,path,col):
        model=widget.get_model()
        v=model[path][0]
        model.remove(model.get_iter(path))
        
        self.colWig[v].set_active(True)
        self.viewTree.get_model().append([v])
        self.preferences.changeVisibility(v,True)
        
    def on_showButton_clicked(self,widget):
        if widget.get_label()=='Show':
            widget=self.hideTree
            func=self.on_hideTree_row_activated
        else:
            widget=self.viewTree
            func=self.on_viewTree_row_activated
            
        treeselection=widget.get_selection()
        (model,iter)=treeselection.get_selected()
        
        try:        
            path=widget.get_model().get_path(iter)
        except:
            return
        
        func(widget,path,0)
        
