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

import os.path,sys
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from twisted.internet import task,reactor
from pkg_resources import resource_string
from p2ner.abstract.ui import UI

levels = {
    "info": 1,
    "warning": 2,
    "error": 3,
    "critical": 4,
    "debug": 0
}

levelColors = {
               'info':'blue',
               'error':'red',
               'warning':'orange',
               'critical':'red'
               }
        
class LoggerGui(UI):
    
    def initUI(self):
        self.loggers=['p2ner']
        self.filters={'peer':[],'level':'debug','log':None}
        self.searchText=None
        self.forward=True
        
        self.cols=[['ip',False],['port',False],['level',True],['log',True],['time',False],['epoch',False],['msecs',False],['module',False],['func',False],['lineno',False],['msg',True]]
        self.ui=None
        self.showing=False
        self.loopingCall = task.LoopingCall(self.getLogEntries)
        try:
            if not self.remote:
                self.frequency=1
            else: 
                self.frequency=3
        except:
            pass
     
    def start(self):
        self.local=True
        if not self.ui:
            self.createGui()
        if not self.showing:
            self.ui.show()
            if self.builder.get_object('pauseButton').get_label()=='Pause':
                self.loopingCall.start(self.frequency)
            self.showing=True
     
    def stop(self):
        self.on_delete_event(self.ui,None)
               
    def createGui(self):     
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'logger.glade'))    
        self.builder.connect_signals(self)
        
        self.ui=self.builder.get_object('ui')
        self.ui.connect('delete-event', self.on_delete_event)
       
        self.builder.get_object('sidePane').set_visible(False) 
        self.tview=self.builder.get_object('treeview')    
        self.tmodel=gtk.ListStore(str,int,str,str,str,float,float,str,str,int,str,str,str,str)
        
        for i in range(len(self.cols)):
            renderer=gtk.CellRendererText()   
            column=gtk.TreeViewColumn(self.cols[i][0],renderer, text=i, foreground=len(self.cols), background=len(self.cols)+1)
            column.set_visible(False) 
            self.tview.append_column(column)
        
        self.tview.show()
        
        self.tfilter=self.tmodel.filter_new()
        self.tfilter.set_visible_func(self.filterFunc)
        
        self.tview.set_model(self.tfilter)
        
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
            menu_item.set_active(col[1])
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
        for i in range(len(self.cols)):
            if self.cols[i][0]==name:
                self.tview.get_column(i).set_visible(widget.get_active())
                break
   
   
    def filterFunc(self,model,iter,data=None):
        if not model.get_value(iter,len(self.cols)):
            return False 
        
        if not self.local and (model.get_value(iter,0),model.get_value(iter,1)) not in self.filters['peer']: 
            if model.get_value(iter,0)!='server':
                return False
        if levels[model.get_value(iter,2).lower()]<levels[self.filters['level'].lower()]:
            return False
        if self.filters['log'] and  self.filters['log']!='p2ner' and model.get_value(iter,3)!=self.filters['log']:
            return False
        return True
    
    def on_forwardButton_toggled(self,widget):
        self.forward=widget.get_active()
             
        
    def setLevel(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        self.level=model[active][0]
        self.filters['level']=model[active][0]
        self.tfilter.refilter()
        
    def setStream(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        self.filters['log']=model[active][0]
        self.tfilter.refilter()

    def getLogEntries(self):
        self.interface.getLogRecords(self.updateView)
    
    def updateView(self,records):
        if not records:
            return
        for r in records:
            clr='black'
            if r['level'].lower() in levelColors.keys():
                clr=levelColors[r['level'].lower()]
            self.tmodel.append((r['ip'],r['port'],r['level'],r['log'],r['time'],r['epoch'],r['msecs'],r['module'],r['func'],r['lineno'],r['msg'],clr,'white','white'))
            if r['log'] not in self.loggers:
                self.addLogger(r['log'])
            if len(self.tfilter):
                self.tview.scroll_to_cell(self.tfilter[-1].path)
        return
    
    
    def on_pauseButton_clicked(self,widget):
        label=widget.get_label()
        if label=='Pause':
            widget.set_label('Start')
            self.loopingCall.stop()
        else:
            widget.set_label('Pause')
            self.loopingCall.start(self.frequency)
            
    def on_exitButton_clicked(self,widget):
        self.stop()
    
    def addLogger(self,logger):
        self.loggers.append(logger)
        self.streamsCombobox.append_text(logger)
        
    def on_searchButton_clicked(self,widget):
        text=self.builder.get_object('searchEntry').get_text()
        if not text:
            self.clearSearch()
            self.searchText=text
            return

        try:
            path=self.tfilter.get_path(self.tview.get_selection().get_selected()[1])
        except:
           path=(0,)

        found=False
        if text!=self.searchText:
            self.clearSearch()
            self.searchText=text
        else:
            path=list(path)
            if self.forward:
                path[0]+=1
            else:
                path[0]-=1
            path=tuple(path)
            
        for m in self.tfilter:
            if text in m[-4]:
                self.tmodel.set_value(self.tfilter.convert_iter_to_child_iter(m.iter),len(self.cols)+1,'orange')
                if not found and (m.path>=path and self.forward) or (m.path<=path and not self.forward):
                    self.tview.get_selection().select_path(m.path)
                    if len(self.tfilter):
                        self.tview.scroll_to_cell(m.path)
                    found=True
            
    def clearSearch(self):
        for m in self.tmodel:
            if m[-2]=='orange':
                m[-2]=m[-1]

    def on_delete_event(self,widget,event):
        if self.loopingCall.running:
            self.loopingCall.stop()
        try:
            self.ui.hide()
        except:
            pass
        self.showing=False
        return True
 
        