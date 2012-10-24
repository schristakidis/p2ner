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
from gtkgui.remotefilechooser import RemoteFileChooser
from p2ner.util.readChannelXML import readChannels
from pkg_resources import resource_string

class dvbFrame(genericFrame):
    
    def __init__(self,parent):

        self.parent=parent
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        """
        try:
            self.builder.add_from_file(os.path.join(path, 'dvbFrame.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'dvbFrame.glade'))
        """
        self.builder.add_from_string(resource_string(__name__, 'dvbFrame.glade'))
        self.builder.connect_signals(self)
        
        self.channelsTreeview = self.builder.get_object("channelsTreeview")
        model=self.channelsTreeview.get_model()
        
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("Name",renderer, text=0,editable=3)
        renderer.connect('edited', self.name_edited_cb,0,model)
        renderer.connect('editing_canceled', self.name_edited_canceled)
        column.set_resizable(True)
        self.channelsTreeview.append_column(column)
        self.nameCol=column
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("Location",renderer, text=1,editable=3)
        renderer.connect('edited', self.location_edited_cb,1,model)
        renderer.connect('editing_canceled', self.location_edited_canceled)
        column.set_resizable(True)
        self.locCol=column
        self.channelsTreeview.append_column(column)
 
        
        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',5)
        column=gtk.TreeViewColumn("Program",renderer, text=2,editable=3)
        renderer.connect('edited', self.program_edited_cb,2,model)
        renderer.connect('editing_canceled', self.program_edited_canceled)
        column.set_resizable(True)
        self.progCol=column
        self.channelsTreeview.append_column(column)
   
        self.channelsTreeview.show()
        
        self.ui = self.builder.get_object("ui")
        self.ui.show()
        self.frame=self.ui
        self.loadChannels()
    
    def name_edited_cb(self,cell,path,text,col,model):
        self.prevEntry=(model[path][col],path,model[path][1])
        if text:
            model[path][col]=text
        else:
            model[path][3]=False
            if self.prevEntry[0]=='':
                model.remove(model.get_iter(path))
            return
        
        self.channelsTreeview.set_cursor(path,self.locCol,start_editing=True)
        p=self.channelsTreeview.get_children()
        p[0].grab_focus()
        
    def name_edited_canceled(self,*p):
        model=self.channelsTreeview.get_model()
        if self.prevEntry[0]=='':
            model.remove(model.get_iter(len(model)-1))
        for m in self.channelsTreeview.get_model():
            m[3]=False
            
    def location_edited_canceled(self,*p):
        if self.channelsTreeview.get_cursor()[0][0]==int(self.prevEntry[1]):
            return
        model=self.channelsTreeview.get_model()
        model[self.prevEntry[1]][0]=self.prevEntry[0]
        if self.prevEntry[0]=='':
            model.remove(model.get_iter(len(model)-1))
        for m in model:
            m[3]=False


    def location_edited_cb(self,cell,path,text,col,model):
        if text:
            model[path][col]=text
        else:
            model[self.prevEntry[1]][0]=self.prevEntry[0]
            if self.prevEntry[0]=='':
                model.remove(model.get_iter(path))
            return
        
        self.channelsTreeview.set_cursor(path,self.progCol,start_editing=True)
        p=self.channelsTreeview.get_children()
        p[0].grab_focus()
                
        
    def program_edited_canceled(self,*p):
        if self.channelsTreeview.get_cursor()[0][0]==int(self.prevEntry[1]):
            return
        model=self.channelsTreeview.get_model()
        model[self.prevEntry[1]][0]=self.prevEntry[0]
        model[self.prevEntry[1]][1]=self.prevEntry[2]
        if self.prevEntry[0]=='':
            model.remove(model.get_iter(len(model)-1))
        for m in model:
            m[3]=False
    
    def program_edited_cb(self,cell,path,text,col,model):
        try:
            text=int(text)
            model[path][col]=text
            model[path][3]=False
        except:
            model[self.prevEntry[1]][0]=self.prevEntry[0]
            model[self.prevEntry[1]][1]=self.prevEntry[2]
            if self.prevEntry[0]=='':
                model.remove(model.get_iter(path))
        

        
        
    
    
    def loadChannels(self,channels=-1):
        model=self.channelsTreeview.get_model() 
        model.clear()
        if channels==-1:
            channels=config.get_channels()
            
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
        model.set_value(iter,3,True)
     
        self.channelsTreeview.set_cursor(path,self.nameCol,start_editing=True)
        p=self.channelsTreeview.get_children()
        p[0].grab_focus()

                                          
    def on_deleteButton_clicked(self,widget):
        treeselection=self.channelsTreeview.get_selection()
        (model, iter) = treeselection.get_selected()
        try:
            path=model.get_path(iter)
        except:
            return
        s=model[path][0]
        model.remove(iter)

            
    def on_newButton_clicked(self,widget):
        model=self.channelsTreeview.get_model()
        model.append(['','',0,True])
        path=len(model)-1
        self.prevEntry=('',0,'')
        self.channelsTreeview.set_cursor(path,self.nameCol,start_editing=True)
        p=self.channelsTreeview.get_children()
        p[0].grab_focus()
              

    def on_loadButton_clicked(self,widget):
        file=self.builder.get_object('fileEntry').get_text()
        if not file:
            return
        
        channels=readChannels(file)
        if not channels:
            return
        self.loadChannels(channels)
        
    def on_browseButton_clicked(self,widget):
        if self.parent.remote:
            self.browseRemote()
        else:
            self.browseLocal()
            
    def browseRemote(self):
        RemoteFileChooser(self.browseFinished,self.parent.interface)
            
    def browseLocal(self):
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
            
    def getChannels(self):
        channels={}
        for s in self.channelsTreeview.get_model():
            channels[s[0]]={}
            channels[s[0]]['location']=s[1]
            channels[s[0]]['program']=s[2]
            
        return channels
            
    def save(self):
        config.writeChannels(self.getChannels())
            
        