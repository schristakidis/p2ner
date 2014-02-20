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
from generic import genericFrame


class statisticsFrame(genericFrame):
    def initUI(self):
        self.frame=gtk.VBox()
        self.buttons={}
        for stat in self.preferences.statsPrefs.keys():
            checkButton=gtk.CheckButton(label="enable "+stat)
            self.buttons[stat]=checkButton
            checkButton.connect('toggled',self.toggled,stat)
            checkButton.show()
            self.frame.pack_start(checkButton,False,False)
        
        self.frame.show()
        self.refresh()

        
    def refresh(self):
        for k,v in self.buttons.items():
            v.set_active(self.preferences.statsPrefs[k]['enabled'])

    def toggled(self,widget,stat):
        self.preferences.statsPrefs[stat]['enabled']=widget.get_active()
        
                
