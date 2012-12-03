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
import pygtk
from twisted.internet import reactor
pygtk.require("2.0")
import gtk
import gobject
from helper import validateIp,validatePort
from generic import genericFrame
from p2ner.util.readChannelXML import readChannels
from pkg_resources import resource_string
from addChannel import AddChannelGui

   
class dvbFrame(genericFrame):
    
    def initUI(self):
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'dvbFrame.glade'))
        self.builder.connect_signals(self)
        
        self.channelsTreeview = self.builder.get_object("channelsTreeview")
        model=self.channelsTreeview.get_model()
        
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("Name",renderer, text=0)
        column.set_resizable(True)
        self.channelsTreeview.append_column(column)
        
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("Location",renderer, text=1)
        column.set_resizable(True)
        self.channelsTreeview.append_column(column)
 
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',5)
        column=gtk.TreeViewColumn("Program",renderer, text=2)
        column.set_resizable(True)
        self.channelsTreeview.append_column(column)
   
        self.channelsTreeview.show()
        
        if self.remote:
            self.builder.get_object('browseButton').set_sensitive(False)
            self.builder.get_object('loadButton').set_sensitive(False)
            
        self.ui = self.builder.get_object("ui")
        self.ui.show()
        self.frame=self.ui
        self.loadChannels()
    
 
        
    
    def loadChannels(self,channels=-1):
        model=self.channelsTreeview.get_model() 
        model.clear()
        if channels==-1:
            channels=self.preferences.getChannels()
            
        if not channels:
            return
        for name in channels.keys():
            model.append((str(name),str(channels[name]['location']),int(channels[name]['program']),False))
        
        

    def on_editButton_clicked(self,widget):
        treeselection=self.channelsTreeview.get_selection()
        try:
            (model, iter) = treeselection.get_selected()
            path=model.get_path(iter)
        except:
            return
     
        self.channelsTreeview.set_sensitive(False)
        AddChannelGui(self.newChannel,model.get_value(iter,0),model.get_value(iter,1),model.get_value(iter,2),iter)

                                          
    def on_deleteButton_clicked(self,widget):
        treeselection=self.channelsTreeview.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path=model.get_path(iter)
        except:
            return
        s=model[path][0]
        self.preferences.removeChannel(s)
        model.remove(iter)

            
    def on_newButton_clicked(self,widget):
        self.channelsTreeview.set_sensitive(False)
        AddChannelGui(self.newChannel)
        return
              
    def newChannel(self,res=None,args=None):
        self.channelsTreeview.set_sensitive(True)
        if not res:
            return
        
        name=res[0]
        loc=res[1]
        prog=res[2]
        model=self.channelsTreeview.get_model()
        
        if not args:
            if  self.checkNewChannel(name):
                model.append((name,loc,prog))
                self.preferences.addChannel(name,loc,prog)
        else:
            iter=args
            old=[]
            old.append(model.get_value(iter,0))
            model.set_value(iter,0,name)
            old.append(model.get_value(iter,1))
            model.set_value(iter,1,loc)
            old.append(model.get_value(iter,2))
            model.set_value(iter,2,prog)
            self.preferences.changeChannel(old,(name,loc,prog))
        
    def checkNewChannel(self,name):
        n=[n for n in self.channelsTreeview.get_model() if name==n[0]]
        if len(n):
            return False
        else:
            return True
        
    def on_loadButton_clicked(self,widget):
        file=self.builder.get_object('fileEntry').get_text()
        if not file:
            return
        
        channels=readChannels(file)
        if not channels:
            return
        self.loadChannels(channels)
        self.preferences.resetChannels(channels)
        
    def on_browseButton_clicked(self,widget):
        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            #print dialog.get_filename(), 'selected'
            filename = dialog.get_filename()           
        elif response == gtk.RESPONSE_CANCEL:
            filename=None
            print 'Closed, no files selected'
        self.browseFinished(filename)
        dialog.destroy()
    
    def browseFinished(self,filename=None):
        if filename:
            self.builder.get_object("fileEntry").set_text(filename)

            

        