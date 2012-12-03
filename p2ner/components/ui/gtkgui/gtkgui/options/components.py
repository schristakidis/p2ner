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

class componentsFrame(genericFrame):
    def initUI(self):
        self.components=self.preferences.components
        
        self.builder = gtk.Builder()

        self.builder.add_from_string(resource_string(__name__, 'optComponents.glade'))
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('componentsFrame')
        self.constructComponents()
        
    def getFrame(self):
        return self.frame
        
    def constructComponents(self):
        for comp in ['input','output','scheduler','overlay']:
            box=self.builder.get_object(('d'+comp+'Combo'))
            self.components[comp]['dcombo'] = gtk.combo_box_new_text()
            self.components[comp]['dcombo'].connect('changed',self.on_component_changed,comp)
            self.components[comp]['dcombo'].set_property('width-request',140)
            box.pack_start(self.components[comp]['dcombo'] ,True,True,0)
            box.show()
            self.components[comp]['dcombo'].show()
            
            default=self.components[comp]['default']    
            i=0
            for sc,v in self.components[comp]['subComp'].items():
                self.components[comp]['dcombo'].append_text(sc)
                if default==sc:
                     found=i
                i+=1
            if found>-1:
                self.components[comp]['dcombo'].set_active(found)

    def on_component_changed(self,widget,comp):
        self.preferences.setTempComponent(comp,widget.get_active_text())
        
 
    
 
    