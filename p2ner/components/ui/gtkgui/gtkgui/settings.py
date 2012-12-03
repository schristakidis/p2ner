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
import hashlib
from time import localtime,mktime
from datetime import datetime
from calendarGui import CalendarGui
from pkg_resources import resource_string
from p2ner.abstract.ui import UI
import copy

class SettingsGui(UI):
    
    def initUI(self,parent=None,show=True):
        self.parent=parent
        self.parametres={}
        self.time=datetime.today()
        self.table={}
        self.entries={}

        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'settingsGui.glade'))
        self.builder.connect_signals(self)
        
        self.ui=self.builder.get_object('ui')

        self.bar = self.builder.get_object("statusbar")
        self.context_id = self.bar.get_context_id('status bar')
        
        overlayBox=self.builder.get_object('overlayBox')
        self.overlayCombobox = gtk.combo_box_new_text()
        overlayBox.pack_start(self.overlayCombobox,True,True,0)
        self.overlayCombobox.show()
        self.getOverlays()
        
        schedulerBox=self.builder.get_object('schedulerBox')
        self.schedulerCombobox = gtk.combo_box_new_text()
        schedulerBox.pack_start(self.schedulerCombobox,True,True,0)
        self.schedulerCombobox.show()
        self.getSchedulers()
        
        inputBox=self.builder.get_object('inputBox')
        self.inputCombobox = gtk.combo_box_new_text()
        inputBox.pack_start(self.inputCombobox,True,True,0)
        self.inputCombobox.show()
        self.getInputs()
        
        
        hoursSpin=self.builder.get_object('hoursButton')
        adjustment = gtk.Adjustment(value=0, lower=0, upper=23, step_incr=1, page_incr=1, page_size=0)
        hoursSpin.configure(adjustment, 1, 0)
        
        minSpin=self.builder.get_object('minsButton')
        adjustment = gtk.Adjustment(value=0, lower=0, upper=59, step_incr=1, page_incr=1, page_size=0)
        minSpin.configure(adjustment, 1, 0)
        
        
        if show:
            self.ui.show()

    def getSchedulers(self):
        self.schedulers=self.preferences.components['scheduler']['subComp']
        default=self.preferences.components['scheduler']['temp']
          
        found=False
        i=0
        self.table['scheduler']={}
        self.schedulerCombobox.get_model().clear()
        for sc in self.schedulers.keys():
            self.schedulerCombobox.append_text(sc)
            self.table['scheduler'][sc]=self.constructTable(sc,self.schedulers[sc])
            if default==sc:
                found=i
            i+=1
        self.schedulerCombobox.connect('changed',self.componentChanged,'schedulerSpecs')
        self.schedulerCombobox.set_active(found)
        
    def getOverlays(self):
        self.overlays=self.preferences.components['overlay']['subComp']
        default=self.preferences.components['overlay']['temp']

        found=False
        i=0
        self.table['overlay']={}
        self.overlayCombobox.get_model().clear()
        for sc in self.overlays.keys():
            self.overlayCombobox.append_text(sc)
            self.table['overlay'][sc]=self.constructTable(sc,self.overlays[sc])
            if default==sc:
                found=i
            i+=1
        self.overlayCombobox.connect('changed',self.componentChanged,'overlaySpecs')
        self.overlayCombobox.set_active(found)
        
    def getInputs(self): 
        self.inputs=self.preferences.components['input']['subComp']
        default=self.preferences.components['input']['temp']
        
        found=False
        i=0
        self.table['input']={}
        self.inputCombobox.get_model().clear()
        for sc in self.inputs.keys():
            self.inputCombobox.append_text(sc)
            self.table['input'][sc]=self.constructTable(sc,self.inputs[sc])
            if default==sc:
                found=i
            i+=1
        self.inputCombobox.connect('changed',self.componentChanged,'inputSpecs')
        self.inputCombobox.set_active(found)
    
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]
    
    def constructTable(self,comp,specs):
        table=gtk.Table(rows=len(specs),columns=2,homogeneous=True)
        i=0
        for k,v in specs.items():  
            label=gtk.Label(v['name'])
            entry=gtk.Entry()
            entry.set_name(k)
            self.entries[(comp,k)]=entry
            entry.set_text(str(v['value']))
            entry.connect('activate',self.entryEdited,None,comp,specs)
            entry.connect('focus-out-event',self.entryEdited,comp,specs)
            table.attach(label,left_attach=0,right_attach=1,top_attach=i,bottom_attach=i+1)
            label.show()
            table.attach(entry,left_attach=1,right_attach=2,top_attach=i,bottom_attach=i+1)
            entry.show()
            tooltip=gtk.Tooltips()
            tooltip.set_tip(label,v['tooltip'])
            i+=1
        table.set_row_spacings(5)
        return table
    
    def componentChanged(self,combobox,boxname):
        comp=self.get_active_text(combobox)
        c=boxname[:-5]
        try:
            table=self.table[c][comp]
        except:
            return
        table.show()

        schSpecs=self.builder.get_object(boxname)
        childs=schSpecs.get_children()
        try:
            schSpecs.remove(childs[0])
        except:
            pass
        schSpecs.pack_start(table,True,True,0)
        
    def entryEdited(self,widget,event,comp,specs):
        par=widget.get_name()
        text=widget.get_text()
        try:
            text=specs[par]['type'](text)
        except:
            text=None
            
        if text is not None:
             specs[par]['tempValue']=text
             self.bar.pop(self.context_id)
        else:
            self.bar.pop(self.context_id)
            self.bar.push(self.context_id, ('supply valid %s'%specs[par]['name']))
            widget.set_text(str(specs[par]['value']))  
        
    def on_timeButton_toggled(self,widget):
        self.builder.get_object('hoursButton').set_sensitive(widget.get_active())
        self.builder.get_object('minsButton').set_sensitive(widget.get_active())
        self.builder.get_object('dateButton').set_sensitive(widget.get_active())
        
    def on_passButton_toggled(self,widget):
        self.builder.get_object('passEntry').set_sensitive(widget.get_active())
            

    def read_parametres(self):
        for component,box,specs in [(self.overlayCombobox,'overlaySpecs',self.overlays),(self.schedulerCombobox,'schedulerSpecs',self.schedulers),(self.inputCombobox,'inputSpecs',self.inputs)]:
            comp=self.get_active_text(component)
            if not comp:
                self.bar.pop(self.context_id)
                self.bar.push(self.context_id, 'missing component')
                return False
            
            self.parametres[box[:-5]]={}
            self.parametres[box[:-5]]['component']=comp
            
            for par in specs[comp].keys():
                v=self.entries[(comp,par)].get_text()
                t=specs[comp][par]['type']
                try:
                    self.parametres[box[:-5]][par]=t(v)
                except:
                    self.bar.pop(self.context_id)
                    self.bar.push(self.context_id, ('supply valid %s'%specs[comp][par]['name']))
                    return False
                
        return True

    def on_resetButton_clicked(self,widget):
        self.getInputs()
        self.getOverlays()
        self.getSchedulers()
        
    def on_saveButton_clicked(self,widget):
        if self.read_parametres():
            self.updateSettings()
            self.preferences.saveSettings()
            
    def on_ui_destroy(self,widget):
        self.ui.destroy()
        
    def on_cancelButton_clicked(self,widget):
        self.ui.destroy()
        
    def on_okButton_clicked(self,widget):
        if not self.read_parametres():
            return
        self.getPassword()
        if not self.getStartTime():
            return
        self.getBools()
        self.ui.destroy()
        self.updateSettings()
        self.parent.setSettings(self.parametres)
 
        
    def updateSettings(self):
        for comp in ('input','overlay','scheduler'):
            for sc in self.preferences.components[comp]['subComp'].keys():
                for par in self.preferences.components[comp]['subComp'][sc].values():
                    if par.has_key('tempValue'):
                        temp=par.pop('tempValue')
                        par['value']=temp

    def getSettings(self):
        if not self.read_parametres():
            return False
        self.getPassword()
        if not self.getStartTime():
            return False
        self.getBools()
        
        self.ui.destroy()
        return self.parametres
    
    def getPassword(self):
        password=None
        if self.builder.get_object('passButton').get_active():
            password=self.builder.get_object('passEntry').get_text()
            p=hashlib.md5()
            p.update(password)
            password=p.digest()
        self.parametres['password']=password
        
    def getStartTime(self):
        start=0
        if self.builder.get_object('timeButton').get_active():
            hour=self.builder.get_object('hoursButton').get_text()
            min=self.builder.get_object('minsButton').get_text()
            self.time=self.time.replace(hour=int(hour),minute=int(min))
            t=self.time.timetuple()
            t=mktime(t)
            now=mktime(localtime())
            start=t
            if t-now<0:
                self.bar.pop(self.context_id)
                self.bar.push(self.context_id, 'not valid start time')
                return False
        self.parametres['startTime']=start
        return True
    
    def getBools(self):
        self.parametres['startable']=self.builder.get_object('startableButton').get_active()
        self.parametres['republish']=self.builder.get_object('republishButton').get_active()

    
        
    def on_dateButton_clicked(self,widget):
        CalendarGui(self)
        
    def setDate(self,date):
        self.time=self.time.replace(year=date[0],month=date[1]+1,day=date[2])