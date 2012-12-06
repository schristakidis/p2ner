import os, stat, time,sys,os.path
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

from twisted.internet import reactor
import pygtk
pygtk.require('2.0')
import gtk
from pkg_resources import resource_string
import os.path

folderxpm = [
    "17 16 7 1",
    "  c #000000",
    ". c #808000",
    "X c yellow",
    "o c #808080",
    "O c #c0c0c0",
    "+ c white",
    "@ c None",
    "@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@",
    "@@+XXXX.@@@@@@@@@",
    "@+OOOOOO.@@@@@@@@",
    "@+OXOXOXOXOXOXO. ",
    "@+XOXOXOXOXOXOX. ",
    "@+OXOXOXOXOXOXO. ",
    "@+XOXOXOXOXOXOX. ",
    "@+OXOXOXOXOXOXO. ",
    "@+XOXOXOXOXOXOX. ",
    "@+OXOXOXOXOXOXO. ",
    "@+XOXOXOXOXOXOX. ",
    "@+OOOOOOOOOOOOO. ",
    "@                ",
    "@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@"
    ]
folderpb = gtk.gdk.pixbuf_new_from_xpm_data(folderxpm)

filexpm = [
    "12 12 3 1",
    "  c #000000",
    ". c #ffff04",
    "X c #b2c0dc",
    "X        XXX",
    "X ...... XXX",
    "X ......   X",
    "X .    ... X",
    "X ........ X",
    "X .   .... X",
    "X ........ X",
    "X .     .. X",
    "X ........ X",
    "X .     .. X",
    "X ........ X",
    "X          X"
    ]
filepb = gtk.gdk.pixbuf_new_from_xpm_data(filexpm)

class RemoteFileChooser(object):
    column_names = ['Name', 'Size', 'Mode', 'Last Changed']

    def delete_event(self, widget, event, data=None):
        self.window.destroy()
        return False
 
    def __init__(self, func,interface,dname = None,onlyDir=False,args=None):
        self.func=func
        self.args=args
        self.interface=interface
        self.onlyDir=onlyDir
        
        # Create a new window

        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'remoteFileChooser.glade'))
        self.builder.connect_signals(self)
        
    
        self.window=self.builder.get_object('window')
        self.window.connect("delete_event", self.delete_event)
        
        self.first=True
        self.make_list(dname)
        
    def setListModel(self,model):
        self.listmodel=model
        if self.first:
            self.makeGui()
            self.first=False
        else:
            self.treeview.set_model(model)
            
    def makeGui(self):
               
        cell_data_funcs = (None, self.file_size, self.file_mode,
                           self.file_last_changed)
        # create the TreeView
        #self.treeview = gtk.TreeView()
        self.treeview=self.builder.get_object('treeview1')
        # create the TreeViewColumns to display the data
        self.tvcolumn = [None] * len(self.column_names)
        cellpb = gtk.CellRendererPixbuf()
        self.tvcolumn[0] = gtk.TreeViewColumn(self.column_names[0], cellpb)
        self.tvcolumn[0].set_cell_data_func(cellpb, self.file_pixbuf)
        cell = gtk.CellRendererText()
        self.tvcolumn[0].pack_start(cell, False)
        self.tvcolumn[0].set_cell_data_func(cell, self.file_name)
        self.treeview.append_column(self.tvcolumn[0])
        for n in range(1, len(self.column_names)):
            cell = gtk.CellRendererText()
            self.tvcolumn[n] = gtk.TreeViewColumn(self.column_names[n], cell)
            if n == 1:
                cell.set_property('xalign', 1.0)
            self.tvcolumn[n].set_cell_data_func(cell, cell_data_funcs[n])
            self.treeview.append_column(self.tvcolumn[n])

        self.treeview.connect('row-activated', self.open_file)
        #self.scrolledwindow = gtk.ScrolledWindow()
        #self.scrolledwindow.add(self.treeview)
        #self.window.add(self.scrolledwindow)
        self.treeview.set_model(self.listmodel)
 
        self.window.show_all()
        return

    def make_list(self,dname=None):
        if not dname:
            dname=False
        self.dirname=dname
        self.interface.requestFiles('requestFiles',dname,self.constructList)
        
    def constructList(self, files):
        self.files={}
        for f in files:
            self.files[f[0]]=f
        
        if self.dirname:    
            self.window.set_title(self.dirname)
        #mfiles = self.files.keys()
        dfiles=[key for key in self.files.keys() if self.files[key][1]]
        
        if not self.onlyDir:
            ffiles=[key for key in self.files.keys() if not self.files[key][1]]
            ffiles.sort()
        else:
            ffiles=[]
            
        dfiles.sort()
        
        mfiles=dfiles+ffiles
        listmodel = gtk.ListStore(object)
        for f in mfiles:
            listmodel.append([f])
        self.setListModel(listmodel)
        
    def open_file(self, treeview, path, column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        file = self.files[model.get_value(iter, 0)]
    
        if file[1]:
            new_model = self.make_list(file[5])
            treeview.set_model(new_model)
        else:
            if not self.args:
                self.func(os.path.abspath(file[5]))
            else:
                self.func(os.path.abspath(file[5]),self.args)
            self.window.destroy()
        return

    def file_pixbuf(self, column, cell, model, iter):
        file = self.files[model.get_value(iter, 0)]
        if file[1]:
            pb = folderpb
        else:
            pb = filepb
        cell.set_property('pixbuf', pb)
        return

    def file_name(self, column, cell, model, iter):
        cell.set_property('text', self.files[model.get_value(iter, 0)][0])
        return

    def file_size(self, column, cell, model, iter):
        size=self.files[model.get_value(iter, 0)][2]
        cell.set_property('text', size)
        return

    def file_mode(self, column, cell, model, iter):
        m=self.files[model.get_value(iter, 0)][4]
        cell.set_property('text', m)
        return


    def file_last_changed(self, column, cell, model, iter):
        t=self.files[model.get_value(iter, 0)][3]
        cell.set_property('text', t)
        return

    def on_closeButton_clicked(self,widget):
        self.window.destroy()
        
    def on_openButton_clicked(self,widget):
        treeselection=self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        file = self.files[model.get_value(iter, 0)]
    
        if not self.onlyDir:
            if file[1]:
                new_model = self.make_list(file[5])
                self.treeview.set_model(new_model)
            else:
                if not self.args:
                    self.func(os.path.abspath(file[5]))
                else:
                    self.func(os.path.abspath(file[5]),self.args)
                self.window.destroy()
        else:
            if not self.args:
                self.func(os.path.abspath(file[5]))
            else:
                self.func(os.path.abspath(file[5]),self.args)
            self.window.destroy()
        return
    
if __name__ == "__main__":
    flcdexample = RemoteFileChooser()
    reactor.run()
