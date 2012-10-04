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
from twisted.internet import task

levels = {
    "info": 1,
    "warning": 2,
    "error": 3,
    "critical": 4,
    "debug": 0
}

class Logger(object):
    def __init__(self,parent):
        self.parent=parent
        self.interface=parent.interface
        self.buffer=[]
        self.loggers=['p2ner']
        self.gui=None
        
    def start(self):
        if not self.gui:
            self.gui=LoggerGui(self,self.interface,self.buffer,self.loggers)
            
    def setBuffer(self,buffer):
        self.buffer=buffer
        self.gui=None
    
    def setLoggers(self,loggers):
        self.loggers=loggers
        
    def stop(self):
        if self.gui:
            self.gui.ui.destroy()
        
class LoggerGui(object):
    
    def __init__(self,parent,interface,buffer,loggers):
        self.parent=parent
        self.interface=interface
        self.loggers=loggers
        self.stream='p2ner'
        self.searchText=''
        self.nextSearchIter=None
        self.buffer=buffer
        infoTag = gtk.TextTag()
        infoTag.set_property('foreground','blue')
        errorTag= gtk.TextTag()
        errorTag.set_property('foreground','red')
        debugTag= gtk.TextTag()
        debugTag.set_property('foreground','black')
        self.tags = {
                  "info": infoTag,
                  "warning": errorTag,
                  "error": errorTag,
                  "critical": errorTag,
                  "debug": debugTag,
                  }
        searchTag = gtk.TextTag('search')
        searchTag.set_property('background','yellow')
        normalTag = gtk.TextTag('normal')
        normalTag.set_property('background','white')
        self.table = gtk.TextTagTable()
        self.table.add(infoTag)
        self.table.add(debugTag)
        self.table.add(errorTag)
        self.table.add(searchTag)
        self.table.add(normalTag)

        self.forward=True
        self.cols=[['levelname',False],['name',False],['asctime',False],['module',False],['funcName',False],['lineno',False]]

        self.createGui()
        
    def createGui(self):     
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'logger.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'logger.glade'))
            
        self.builder.connect_signals(self)
        
        self.ui=self.builder.get_object('ui')

        self.tview=self.builder.get_object('textview')    
        self.tbuffer=gtk.TextBuffer(self.table)
        self.tview.set_buffer(self.tbuffer)
        
        
        levelsBox=self.builder.get_object('levelsBox')
        levelsCombobox = gtk.combo_box_new_text()
        levelsBox.pack_start(levelsCombobox,True,True,0)
        levelsCombobox.show()
        
        for level in levels.keys():
            levelsCombobox.append_text(level)
        levelsCombobox.connect('changed',self.setLevel)
        levelsCombobox.set_active(1)
        
        streamsBox=self.builder.get_object('streamsBox')
        self.streamsCombobox = gtk.combo_box_new_text()
        streamsBox.pack_start(self.streamsCombobox,True,True,0)
        self.streamsCombobox.show()

        for log in self.loggers:
            self.streamsCombobox.append_text(log)
        self.streamsCombobox.set_active(0)
        self.streamsCombobox.connect('changed',self.setStream)
        


        self.createMenu()
        self.ui.show()
        self.loopingCall = task.LoopingCall(self.getLogEntries)
        if not self.parent.parent.remote:
            f=0.1
        else:
            f=3
        self.loopingCall.start(3)
        

    def createMenu(self):
        #create menu bar
        menu_bar=gtk.MenuBar()
        menu_bar.show()
        vbox=self.builder.get_object("menuBox")
        vbox.pack_start(menu_bar,False,False,0)
        
        ###create view menu
        collumnsItem=gtk.MenuItem('collumns')
        collumnsItem.show()
        
        viewMenu=gtk.Menu()
        viewMenu.append(collumnsItem)

        ###create columns menu
        collumnsMenu=gtk.Menu()                
    
        for col in self.cols:
            menu_item=gtk.CheckMenuItem(col[0])
            menu_item.connect('toggled',self.on_col_toggled)
            menu_item.show()
            collumnsMenu.append(menu_item)
        
        collumnsItem.set_submenu(collumnsMenu)
        self.visibleCollumns=collumnsMenu
        
        root_menu=gtk.MenuItem('View')
        root_menu.show()
        root_menu.set_submenu(viewMenu)
        menu_bar.append(root_menu)
        
    def on_col_toggled(self,widget):
        name=widget.get_label()
        for col in self.cols:
            if col[0]==name:
                col[1]=not col[1]
                break
        self.refilter()
        
    def on_forwardButton_toggled(self,widget):
        self.forward=widget.get_active()
             
        
    def setLevel(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        self.level=model[active][0]
        self.refilter()
        
    def setStream(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        self.stream=model[active][0]
        self.searchText=None
        self.refilter()
        
        
    def refilter(self):
        self.tbuffer=gtk.TextBuffer(self.table)
        self.tview.set_buffer(self.tbuffer)
        for r in self.buffer:
            if self.filter(r):
                enditer = self.tbuffer.get_end_iter()
                text,tag = self.printRecord(r)
                self.tbuffer.insert_with_tags(enditer,text,tag)
                self.tview.scroll_to_mark(self.tbuffer.get_insert(),0)

            
    def filter(self,record):
        if levels[self.level]<=levels[record.levelname.lower()]:
            if self.stream==record.name or self.stream=='p2ner':
                return True
        return False
    
    def getLogEntries(self):
        self.interface.send('getRecords',None,self.updateView)
    
    def updateView(self,records):
        for r in records:
            if r.name not in self.loggers:
                self.addLogger(r.name)
            if self.filter(r):
                enditer = self.tbuffer.get_end_iter()
                text,tag = self.printRecord(r)
                self.tbuffer.insert_with_tags(enditer,text,tag)
                self.tview.scroll_to_mark(self.tbuffer.get_insert(),0)
            self.buffer.append(r)
        
        
    def printRecord(self,record):
        r=[str(eval('record.'+str(p[0]))) for p in self.cols if p[1]]
        try:
            r.append(record.getMessage())
            ret=' '.join(r)+'\n'
            tag=self.tags[record.levelname.lower()]
        except:
            ret='error in logger'
            tag=self.tags['error']
        return (ret,tag)
    
    def on_pauseButton_clicked(self,widget):
        label=widget.get_label()
        if label=='Pause':
            widget.set_label('Start')
            self.loopingCall.stop()
        else:
            widget.set_label('Pause')
            self.loopingCall.start(0.1)
            
    def on_exitButton_clicked(self,widget):
        self.ui.destroy()
        

    def on_ui_destroy(self,data=None):
        self.loopingCall.stop()
        self.parent.setLoggers(self.loggers)
        self.parent.setBuffer(self.buffer)
            
    def addLogger(self,logger):
        self.loggers.append(logger)
        self.streamsCombobox.append_text(logger)
        
    def on_searchButton_clicked(self,widget):
        text=self.builder.get_object('searchEntry').get_text()
        if not text:
            #print 'returningggggggggg'
            self.searchText=text
            return
        if text!=self.searchText:
            startiter = self.tbuffer.get_start_iter()
            enditer = self.tbuffer.get_end_iter()
            renditer = self.tbuffer.get_start_iter()
            rstartiter = self.tbuffer.get_end_iter()
            self.tbuffer.remove_tag_by_name('search', startiter, enditer)
            self.searchText=text
        else:
            startiter=self.nextSearchIter
            rstartiter=self.nextSearchIter
            #print 'should search the same again'
        
        if self.forward:
            try:    
                start,self.nextSearchIter = startiter.forward_search(text,gtk.TEXT_SEARCH_VISIBLE_ONLY)
            except:
                #print 'no other instances'
                return
        else:
            try:
                self.nextSearchIter,start = rstartiter.backward_search(text,gtk.TEXT_SEARCH_VISIBLE_ONLY)
            except:
                #print 'no other instances'
                return
        self.tbuffer.apply_tag_by_name('search', start, self.nextSearchIter)
        self.tview.scroll_to_iter(start, 0)
        