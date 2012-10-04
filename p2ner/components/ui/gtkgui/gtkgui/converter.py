import pygtk
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

pygtk.require("2.0")
import gtk
import gobject
import os.path,sys
from twisted.internet import reactor,task


class ConverterGui(object):
    def __init__(self,parent,settings):
        self.parent=parent
        self.settings=settings
        self.id=None
        self.loopingCall = task.LoopingCall(self.poll)

        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'converter.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'converter.glade'))
            
        self.builder.connect_signals(self)
        
        filename=self.settings['filename']
        
        self.builder.get_object('descLabel').set_text(('Converting file %s'%os.path.basename(settings['filename'])))
        
        self.ui=self.builder.get_object('ui')
        self.ui.show()
        
        
        dir=self.parent.preferences.getCdir()

        self.settings['filename']=os.path.join(dir,os.path.basename(filename))
        self.settings['type']='cfile'
        videoRate=int(self.settings['input']['videoRate'])
        subs=self.settings['input']['advanced']['subs']
        subsFile=''
        subsEnc=''
        if subs:
            subsFile=self.settings['input']['advanced']['subsFile']
            subsEnc=self.settings['input']['advanced']['encoding']
            
        self.parent.interface.startConverting(self,dir,filename,videoRate,subs,subsFile,subsEnc)
        
    def getConverterId(self,id):
        self.id=id
        self.loopingCall.start(1)
        
    def poll(self):
        self.parent.interface.getConverterStatus(self,self.id)
        
    def setStatus(self,status):
        if status>=0:
            self.builder.get_object('progressLabel').set_text(str(status))
        elif status==-1:
            self.loopingCall.stop()
            self.ui.destroy()
            self.parent.registerStreamSettings(self.settings)
        
        
    def on_hideButton_clicked(self,widget):
        self.ui.destroy()
        
    def on_abortButton_clicked(self,widget):
        self.loopingCall.stop()
        self.ui.destroy()
        self.parent.interface.abortConverter(self.id)
    


        