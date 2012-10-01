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
from subcomp import subcompFrame

class inputFrame(subcompFrame):
    def __init__(self,parent):
        self.parent=parent
        self.settings={}
        self.component='input'
        self.constructNotebook()
        
class outputFrame(subcompFrame):
    def __init__(self,parent):
        self.parent=parent
        self.settings={}
        self.component='output'
        self.constructNotebook()
        
class schedulerFrame(subcompFrame):
    def __init__(self,parent):
        self.parent=parent
        self.settings={}
        self.component='scheduler'
        self.constructNotebook()
        
class overlayFrame(subcompFrame):
    def __init__(self,parent):
        self.parent=parent
        self.settings={}
        self.component='overlay'
        self.constructNotebook()