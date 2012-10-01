import os, sys
from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except:
    pass
from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
from remotefilechooser import RemoteFileChooser
from p2ner.util.utilities import get_user_data_dir
from plot import PlotGui

class statsGui(object):
    def __init__(self,interface=None,remote=False):
        self.interface=interface
        self.remote=remote
        self.selectedStats=[]
        self.combine=False
        self.file=None
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'stats.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'stats.glade'))

        self.builder.connect_signals(self)
        
        self.ui = self.builder.get_object("ui")
        
        self.statsTreeview = self.builder.get_object("treeview")
        model=self.statsTreeview.get_model()

        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("statistic",renderer, text=0)
        column.set_resizable(True)
        self.statsTreeview.append_column(column)

        renderer=gtk.CellRendererToggle()
        column=gtk.TreeViewColumn("add",renderer, active=1)
        renderer.connect("toggled", self.toggled_cb, model)
        column.set_resizable(True)
        self.statsTreeview.append_column(column)
        
        renderer=gtk.CellRendererText()
        renderer.set_property( 'editable', True )
        renderer.connect( 'edited', self.col0_edited_cb, model )
        column=gtk.TreeViewColumn("scale",renderer, text=2)
        column.set_resizable(True)
        
        self.statsTreeview.append_column(column)
   
        self.statsTreeview.show()
        
        self.builder.get_object('showButton').set_sensitive(False)
        
        if self.remote:
            self.builder.get_object('openButton').set_sensitive(False)
            
        if not self.interface:
            self.builder.get_object('refreshButton').set_sensitive(False)
            self.builder.get_object('liveButton').set_sensitive(False)
        else:
            self.builder.get_object('liveButton').set_active(True)
            self.builder.get_object('liveButton').set_sensitive(False)
            
        self.builder.get_object('fileEntry').set_editable(False)
        self.file=False    
        self.ui.show()
            
    def col0_edited_cb( self, cell, path, new_text, model ):
        try:
            model[path][2]=float(new_text)
        except:
            pass

    def toggled_cb(self,cell, path, user_data):
        model = user_data
        model[path][1] = not model[path][1]
        if model[path][1]:
            self.selectedStats.append(model[path][0])
            self.builder.get_object('showButton').set_sensitive(True)
        else:
            self.selectedStats.remove(model[path][0])
            if not len(self.selectedStats):
                self.builder.get_object('showButton').set_sensitive(False)
                
    def on_stackButton_toggled(self,widget):
        self.combine=widget.get_active()
                
        
    def on_liveButton_toggled(self,widget):
        if widget.get_active():
            self.file=None
            self.on_refreshButton_clicked()
            self.builder.get_object('fileEntry').set_text('')
            self.builder.get_object('liveButton').set_sensitive(False)
               
    def on_openButton_clicked(self,widget,data=None):
        if self.remote:
            self.browseRemote()
        else:
            self.browseLocal()
            
    def browseRemote(self):
        RemoteFileChooser(self.browseFinished,self.interface,dname=get_user_data_dir())
            
    def browseLocal(self):
        filter=gtk.FileFilter()
        filter.set_name('stat files')
        filter.add_pattern('*.stat')

        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        if not dialog.set_current_folder(os.path.join(get_user_data_dir(),'stats')):
             dialog.set_current_folder(get_user_data_dir())
       
        dialog.add_filter(filter)

        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            #print dialog.get_filename(), 'selected'
            filename = dialog.get_filename()           
        elif response == gtk.RESPONSE_CANCEL:
            filename=None
            print 'Closed, no files selected'
        self.browseFinished(filename)
        dialog.destroy()
    
    def browseFinished(self,filename=None):
        if filename:
            self.file=filename
            self.builder.get_object("liveButton").set_active(False)
            self.builder.get_object("liveButton").set_sensitive(True)
            self.builder.get_object("fileEntry").set_text(os.path.basename(filename))
            self.builder.get_object('showButton').set_sensitive(False)
            self.selectedStats=[]
            f=open(filename,'r')
            model=self.statsTreeview.get_model()
            model.clear()
            for s in f.readlines():
                model.append([s,False,1.0])
            
    def on_refreshButton_clicked(self,widget=None):
        self.interface.getAvailableStatistics(self.newStats)
        
    def newStats(self,stats):
        model=self.statsTreeview.get_model()
        model.clear()
        for s in stats:
            model.append((s,False,1))
            
    def on_ui_destroy(self,widget=None,data=None):
        if not self.interface:
            try:
                reactor.stop()
            except:
                pass
            
    def on_closeButton_clicked(self,widget):
        self.ui.destroy()
        self.on_ui_destroy()
        
    def on_showButton_clicked(self,widget):
        model=self.statsTreeview.get_model()
        stats=[]
        for s in model:
            if s[1]:
                stats.append((s[0],s[2]))
        PlotGui(stats,self.interface,self.file,self.combine)

if __name__=='__main__':
    statsGui()
    reactor.run()
    

        