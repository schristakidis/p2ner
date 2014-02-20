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
from subcomp import subcompFrame

class inputFrame(subcompFrame):
    def initUI(self):
        self.component='input'
        self.settings=self.preferences.components[self.component]['subComp']
        self.constructNotebook()
        
class outputFrame(subcompFrame):
    def initUI(self):
        self.component='output'
        self.settings=self.preferences.components[self.component]['subComp']
        self.constructNotebook()
        
class schedulerFrame(subcompFrame):
    def initUI(self):
        self.component='scheduler'
        self.settings=self.preferences.components[self.component]['subComp']
        self.constructNotebook()
        
class overlayFrame(subcompFrame):
    def initUI(self):
        self.component='overlay'
        self.settings=self.preferences.components[self.component]['subComp']
        self.constructNotebook()
