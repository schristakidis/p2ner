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
import copy

class subcompFrame(genericFrame):
    def initUI(self):
        pass
         
    def constructNotebook(self):
        self.entries={}

        self.notebook=gtk.Notebook()
        for comp in self.settings.keys():
            label=gtk.Label(comp)
            label.show()
            page=self.constructPage(comp)
            if page:    
                self.notebook.append_page(page,label)
        self.notebook.show()
        self.frame=self.notebook
        
    def constructPage(self,comp):
        if not len(self.settings[comp]):
            table=gtk.Label()
            table.set_text('there are no parametres to set for this component')
            table.show()
            return table

        hbox=gtk.VBox()
        hbox.show()
        table=gtk.Table(rows=len(self.settings[comp]),columns=2,homogeneous=True)

        i=0
        for k,v in self.settings[comp].items():   
            label=gtk.Label(v['name'])
            entry=gtk.Entry()
            entry.set_name(k)
            entry.set_text(str(v['value']))
            self.entries[(comp,k)]=entry
            entry.connect('activate',self.entryEdited,None,comp)
            entry.connect('focus-out-event',self.entryEdited,comp)
            table.attach(label,left_attach=0,right_attach=1,top_attach=i,bottom_attach=i+1)
            label.show()
            table.attach(entry,left_attach=1,right_attach=2,top_attach=i,bottom_attach=i+1)
            entry.show()
            tooltip=gtk.Tooltips()
            tooltip.set_tip(label,v['tooltip'])
            i+=1
        table.set_row_spacings(5)
        table.show()
        
        hbox.pack_start(table,False,False,0)
        

        l=gtk.Label()
        l.show()
        hbox.pack_start(l,True,True,0)
        hbox.set_border_width(20)

        return hbox
        
    def entryEdited(self,widget,event,comp):
        par=widget.get_name()
        text=widget.get_text()
        try:
            text=self.settings[comp][par]['type'](text)
        except:
            text=None
            
        if text is not None:
             self.settings[comp][par]['value']=text
        else:
            widget.set_text(str(self.settings[comp][par]['value']))       
    
                
    def setDefaults(self):
        for comp,interface in self.parent.components[self.component].items():
            if comp!='dcombo':
                try:
                    platform=interface.platform
                except:
                    platform=None
                
                if platform and platform not  in sys.platform:
                    continue

                for k,v in interface.specs.items():
                    self.settings[comp][k]['value']=interface.specs[k]
          
        self.reloadEntries()
        
    def reloadEntries(self):
        for comp in self.settings.keys():
            for par in self.settings[comp].keys():
                self.entries[(comp,par)].set_text(str(self.settings[comp][par]['value']))
                
    def updateSettings(self,settings):
        self.settings=copy.deepcopy(settings)
        self.reloadEntries()
           
    def refresh(self):
        self.reloadEntries()
        
                

        

