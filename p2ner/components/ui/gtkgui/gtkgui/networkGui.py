import os, sys
import os.path
import pygtk
pygtk.require("2.0")
import gtk
import gobject


class NetworkGui(object):
    def __init__(self,parent):
        self.parent=parent
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'networkGui.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'networkGui.glade'))
            
        self.builder.connect_signals(self)
            
        self.tview=self.builder.get_object('textview')    
        self.tbuffer=gtk.TextBuffer()
        self.tview.set_buffer(self.tbuffer)
        
        self.addText('Checking network conditions...')

        self.ui=self.builder.get_object('ui')
        #self.ui.show()
        
    def show(self):
        self.ui.show()
        
    def addText(self,text):
        text +='\n'
        self.tbuffer.insert(self.tbuffer.get_end_iter(),text)
        self.tview.scroll_to_mark(self.tbuffer.get_insert(),0)
        
    def on_closeButton_clicked(self,widget):
        self.parent.preferences.setCheckNetAtStart(self.builder.get_object('startUpButton').get_active())
        self.ui.destroy()
        
    def on_startUpButton_toggled(self,widget):
        print 'on start :',widget.get_active()