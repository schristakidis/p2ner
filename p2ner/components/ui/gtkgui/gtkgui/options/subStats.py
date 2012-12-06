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
from gtkgui.remotefilechooser import RemoteFileChooser

class statFrame(genericFrame):
    def constructFrame(self):
        self.frame=gtk.VBox()
        self.frame.set_border_width(20)
        self.frame.set_spacing(10)
        for k,v in self.settings.items():
            if v.has_key('gtype'):
                type=v['gtype']
            else:
                type=str(v['type'])
            
            if type=='check':
                box=gtk.HBox()
                check=gtk.CheckButton(label=v['name'])
                check.show()
                box.pack_start(check,False,False)
                tooltip=gtk.Tooltips()
                tooltip.set_tip(check,v['tooltip'])
                check.connect('toggled',self.toggled,v)
                box.show()
                self.fields[check]={'check':True,'par':k}
                self.frame.pack_start(box,False,False)
            elif 'browse' in type:
                box=gtk.VBox()
                box.show()
                hbox=gtk.HBox()
                hbox.show()
                box.pack_start(hbox,False,False)
                l=gtk.Label(v['name'])
                l.show()
                hbox.pack_start(l,False,False)
                hbox=gtk.HBox()
                hbox.show()
                box.pack_start(hbox,False,False)
                entry=gtk.Entry()
                entry.set_sensitive(False)
                entry.show()
                tooltip=gtk.Tooltips()
                tooltip.set_tip(entry,v['tooltip'])
                self.fields[entry]={'check':False,'par':k}
                hbox.pack_start(entry,True,True)
                button=gtk.Button(label='Browse')
                dir=False
                if 'Dir' in type:
                    dir=True
                button.connect('clicked',self.browse,v,dir)
                button.show()
                hbox.pack_end(button,False,False)
                self.frame.pack_start(box,False,False)
            else:
                box=gtk.HBox()
                box.show()
                l=gtk.Label(v['name'])
                l.show()
                box.pack_start(l,False,False)
                entry=gtk.Entry()
                entry.set_sensitive(True)
                entry.show()
                entry.connect('activate',self.entryEdited,None,v)
                entry.connect('focus-out-event',self.entryEdited,v)
                tooltip=gtk.Tooltips()
                tooltip.set_tip(entry,v['tooltip'])
                self.fields[entry]={'check':False,'par':k}
                box.pack_end(entry,False,False)
                self.frame.pack_start(box,False,False)
                
        self.frame.show()
        
    def refresh(self):
        for k,v in self.fields.items():
            if v['check']:
                active=self.settings[v['par']]['value']
                if active:
                    k.set_active(True)
                else:
                    k.set_active(False)
            else:
                k.set_text(str(self.settings[v['par']]['value']))
    
    def browse(self,widget,par,dir):
        if not self.remote:
            self.browseLocally(par,dir)
        else:
            RemoteFileChooser(self.browseFinished,self.interface,onlyDir=dir,args=par)
            
    def browseLocally(self,par,onlydir):
        if not onlydir:
            action=gtk.FILE_CHOOSER_ACTION_OPEN
        else:
            action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER
   
        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               action,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
 
            
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()       
            self.browseFinished(filename,par)    
            
        elif response == gtk.RESPONSE_CANCEL:
            filename=None

        
        dialog.destroy()
        
    def browseFinished(self,filename,par):
        if filename:
            par['value']=filename
            self.refresh()
            
    def toggled(self,widget,par):
        par['value']=widget.get_active()

    
    def entryEdited(self,widget,event,par):
        text=widget.get_text()
        try:
            text=par['type'](text)
        except:
            text=None
            
        if text is not None:
             par['value']=text
        else:
            widget.set_text(str(par['value']))   
       
class filestatsFrame(statFrame):
    def initUI(self):
        self.fields={}
        self.statistic='FileStats'
        self.settings=self.preferences.statsPrefs[self.statistic]['par']
        self.constructFrame()

       