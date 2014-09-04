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
from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
from remotefilechooser import RemoteFileChooser
from p2ner.util.utilities import get_user_data_dir
from plot import PlotGui
from pkg_resources import resource_string
from p2ner.abstract.ui import UI
from plotGui import PlotGui
from copy import deepcopy
from statsdb import DB
from cPickle import loads,dumps,load,dump

class statsGui(UI):
    def initUI(self):
        self.makingNewGraph=False
        self.statinGraph=False
        self.liveMode=True
        self.localdb=None

        if not self.parent.remote:
            for s in self.root.__stats__:
                if 'db' in s:
                    self.statCollector=s

        self.getStatKeys()

        self.plots={}
        self.pid=0
        self.showing=True

        path = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'stats.glade'))
        self.builder.connect_signals(self)

        self.ui = self.builder.get_object("ui")
        self.ui.set_title('Statistics')

        self.ui.connect('delete-event', self.on_delete_event)

        ######## MENU
        menuBar=gtk.MenuBar()

        fileMenu=gtk.Menu()
        menu_item=gtk.MenuItem('Load')
        menu_item.connect('activate',self.on_loadButton_clicked)
        menu_item.show()

        fileMenu.append(menu_item)


        menu_item=gtk.MenuItem('Load Template')
        # menu_item.connect('select',self.on_loadTButton_clicked)
        menu_item.show()

        subMenu=gtk.Menu()
        menu_item.set_submenu(subMenu)
        subMenu.show()

        subMenu.connect('show',self.on_loadTButton_clicked)
        fileMenu.append(menu_item)

        menu_item=gtk.MenuItem('Save Template')
        menu_item.connect('activate',self.on_saveTButton_clicked)
        menu_item.show()

        fileMenu.append(menu_item)

        root_menu=gtk.MenuItem('File')
        root_menu.show()
        root_menu.set_submenu(fileMenu)
        menuBar.append(root_menu)
        menuBar.show()

        self.builder.get_object('vbox1').pack_start(menuBar,False,False)
        #component
        self.componentTreeview = self.builder.get_object("compTreeview")
        model=self.componentTreeview.get_model()

        renderer=gtk.CellRendererText()
        renderer.set_property('width-chars',30)
        renderer.set_property('xpad',10)
        # renderer.connect("row-activated", self.componentSelected, model)
        column=gtk.TreeViewColumn("component",renderer, text=0)
        column.set_resizable(True)
        # column.set_fixed_width(120)
        self.componentTreeview.append_column(column)

        # self.componentTreeview.connect("row-activated", self.componentSelected, model)
        self.componentTreeview.get_selection().connect("changed",self.componentSelected)
        self.componentTreeview.show()

        #sid
        self.sidTreeview = self.builder.get_object("sidTreeview")
        model=self.sidTreeview.get_model()

        renderer=gtk.CellRendererText()
        renderer.set_property('xpad',10)
        renderer.set_property('width-chars',10)
        # renderer.connect("row-activated", self.sidSelected, model)
        column=gtk.TreeViewColumn("sid",renderer, text=0)
        column.set_resizable(True)
        # column.set_fixed_width(10)
        self.sidTreeview.append_column(column)
        # self.sidTreeview.connect("row-activated", self.sidSelected, model)
        self.sidTreeview.get_selection().connect("changed",self.sidSelected)

        self.sidTreeview.show()

        #stats
        self.statsTreeview = self.builder.get_object("statsTreeview")
        model=self.statsTreeview.get_model()

        renderer=gtk.CellRendererText()
        # renderer.set_property('xpad',10)
        renderer.set_property('width-chars',30)
        column=gtk.TreeViewColumn("statistic",renderer, text=0)
        column.set_resizable(True)
        self.statsTreeview.connect("row-activated", self.statSelected, model)
        # column.set_fixed_width(60)
        self.statsTreeview.append_column(column)

        self.statsTreeview.show()

        self.newGraphBox=self.builder.get_object('newGraphBox')
        scrolSub=self.builder.get_object('scrolSub')

        self.subBox=gtk.VBox()#self.builder.get_object('subBox')
        scrolSub.add_with_viewport(self.subBox)
        self.subBox.show()
        self.initStats()
        self.ui.show()
        if self.parent.remote:
            self.builder.get_object('refreshButton').set_sensitive(False)

    def getStatKeys(self):
        if not self.parent.remote:
            self.statKeys=self.statCollector.getAvailableStats()
        else:
            self.statKeys=[]

    def initStats(self):
        model=self.componentTreeview.get_model()
        model.clear()
        for k in self.statKeys:
            model.append((k,))
        if self.statKeys:
            self.componentTreeview.get_selection().select_path((0,))


    def componentSelected(self,selection):#treeview,path,col,model):
        try:
            path=selection.get_selected_rows()[1][0]
        except:
            return
        model=self.componentTreeview.get_model()
        comp=model[path][0]
        model=self.sidTreeview.get_model()
        model.clear()
        for sid in self.statKeys[comp]:
            model.append((sid,))
        if self.statKeys[comp]:
            self.sidTreeview.get_selection().select_path((0,))

    def sidSelected(self,selection):#treeview,path,col,model):
        path=selection.get_selected_rows()[1]
        try:
            path=path[0]
        except:
            return
        model=self.sidTreeview.get_model()
        sid=model[path][0]

        model=self.statsTreeview.get_model()
        model.clear()
        compRow=self.componentTreeview.get_selection().get_selected_rows()[1][0]
        compModel=self.componentTreeview.get_model()
        comp=compModel[compRow][0]
        for stat in self.statKeys[comp][sid]:
            model.append((stat,))


    def statSelected(self,treeview,path,col,model):
        if not self.makingNewGraph:
            return

        if not self.statinGraph:
            self.statinGraph=True

        compRow=self.componentTreeview.get_selection().get_selected_rows()[1][0]
        comp=self.componentTreeview.get_model()[compRow][0]

        idRow=self.sidTreeview.get_selection().get_selected_rows()[1][0]
        sid=self.sidTreeview.get_model()[idRow][0]

        stat=model[path][0]

        if (comp,sid,stat) in self.newSubGraph:
            return
        self.newSubGraph.append((comp,sid,stat))
        self.lStore.append((stat,))

    def on_newButton_clicked(self,widget):
        self.newGraphBox.set_visible(True)
        self.newGraph={}
        self.newSubGraph=[]
        self.subCount=0
        children=self.subBox.get_children()
        for child in children:
            self.subBox.remove(child)
        widget.set_sensitive(False)
        self.ui.resize(1,1)
        self.on_sub_clicked(None)

    def on_sub_clicked(self,widget):
        if self.subCount:
            if not self.newSubGraph:
                return
            self.newGraph[self.subCount]['stats']=self.newSubGraph
            self.newSubGraph=[]
        if not self.makingNewGraph:
            self.makingNewGraph=True
            self.sharedButton=gtk.CheckButton('sharedX')
            self.subBox.pack_start(self.sharedButton,False,False)
            self.sharedButton.show()
        else:
            l=gtk.Label('------------------')
            l.show()
            self.subBox.pack_start(l,False,False)

        textEntry=gtk.Entry()
        textEntry.set_text('SubGraph'+str(self.subCount))
        self.subCount+=1
        self.subBox.pack_start(textEntry,False,False)
        textEntry.show()
        self.newGraph[self.subCount]={}
        self.newGraph[self.subCount]['name']=textEntry

        h=gtk.HBox()
        l=gtk.Label('X axis:')
        h.pack_start(l)
        l.show()
        combo=gtk.combo_box_entry_new_text()
        combo.append_text('customX')
        combo.append_text('lpb')
        combo.append_text('time')
        combo.set_active(0)
        combo.get_children()[0].set_editable(False)
        combo.show()
        h.pack_start(combo,True,True)
        h.show()
        self.subBox.pack_start(h,False,False)
        self.newGraph[self.subCount]['x']=combo

        hbox=gtk.HBox()
        self.lStore=gtk.ListStore(str)
        tview=gtk.TreeView(self.lStore)
        hbox.pack_start(tview,True,True)
        renderer=gtk.CellRendererText()
        # renderer.set_property('width-chars',30)
        # renderer.set_property('xpad',10)
        column=gtk.TreeViewColumn("statistics",renderer, text=0)
        column.set_resizable(True)
        # column.set_fixed_width(120)
        tview.append_column(column)

        tview.show()
        hbox.show()

        self.subBox.pack_start(hbox,False,False)



    def on_subOk_clicked(self,widget):
        if not self.statinGraph:
            return

        if self.newSubGraph:
            self.newGraph[self.subCount]['stats']=self.newSubGraph
        else:
            del self.newGraph[self.subCount]
        for k,v in self.newGraph.items():
            self.newGraph[k]['name']=v['name'].get_text()
            self.newGraph[k]['x']=v['x'].get_active_text()
        self.makeGraph()
        self.on_subCancel_clicked(widget)


    def on_subCancel_clicked(self,widget):
        self.makingNewGraph=False
        self.statinGraph=False
        self.newGraphBox.set_visible(False)
        self.builder.get_object('newButton').set_sensitive(True)
        self.ui.resize(1,1)


    def on_refreshButton_clicked(self,widget=None):
        self.liveMode=True
        if self.localdb:
            self.localdb.stop()
        self.getStatKeys()
        self.initStats()


    def makeGraph(self):
        stats=[]
        sharedx=self.sharedButton.get_active()
        plot={}
        for k,v in self.newGraph.items():
            plot[v['name']]=[]
            for s in v['stats']:
                plot[v['name']].append(s)
                if s not in stats:
                    stats.append(s)

        if self.liveMode:
            self.makeLiveGraph(stats,sharedx)
        else:
            self.makeFileGraph(stats,sharedx)

    def makeLiveGraph(self,stats,sharedx):
        newPlot= PlotGui(self.pid,deepcopy(self.newGraph),sharedx,self.statCollector.getStats,_parent=self)
        self.plots[self.pid]=newPlot
        self.statCollector.subscribe(newPlot,newPlot.updatePlots,stats)
        self.pid+=1

    def makeFileGraph(self,stats,sharedx):
        newPlot= PlotGui(self.pid,deepcopy(self.newGraph),sharedx,None,_parent=self)
        self.plots[self.pid]={}
        self.plots[self.pid]['plot']=newPlot
        for s in stats:
            self.plots[self.pid][s]=-1
            d=self.localdb.getStats(s)
            d.addCallback(self.retFileValues,self.pid)
        self.pid+=1

    def plotDestroyed(self,plot):
        if plot not in self.plots:
            return
        if not type(self.plots[plot])==dict:
            self.statCollector.unsubscribe(self.plots[plot])
        del self.plots[plot]

    def on_closeButton_clicked(self,widget):
        self.ui_hide()

    def ui_destroy(self):
        self.ui.destroy()

    def ui_hide(self):
        self.ui.hide()
        self.showing=False

    def ui_show(self):
        self.ui.show()
        self.showing=True

    def on_delete_event(self,widget,event):
        try:
            self.ui_hide()
        except:
            pass
        return True

    def on_loadButton_clicked(self,widget,data=None):
        if self.makingNewGraph:
            print "you can't load file while making new Graph"
            return
        if self.parent.remote:
            self.browseRemote()
        else:
            self.browseLocal()

    def browseRemote(self):
        RemoteFileChooser(self.getRemoteFileStat,self.parent.interface,dname=get_user_data_dir())

    def getRemoteFileStat(self,filename):
        if not filename:
            return
        baseFile=os.path.basename(filename)
        # targetFile=os.path.join(get_user_data_dir(),'stats')
        targetFile=get_user_data_dir()

        targetFile=os.path.join(targetFile,'r'+baseFile)

        d=self.parent.interface.copyStatFile(filename)
        d.addCallback(self.writeRemoteStatFile,targetFile)

    def writeRemoteStatFile(self,rFile,targetFile):
        f=open(targetFile,'wb')
        rFile=loads(rFile)
        for line in rFile:
            f.write(line)
        f.close()
        self.browseFinished(targetFile)


    def browseLocal(self):
        filter=gtk.FileFilter()
        filter.set_name('stat files')
        filter.add_pattern('*.db')

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
        dialog.destroy()
        self.browseFinished(filename)

    def browseFinished(self,filename=None):
        if not filename:
            return
        self.liveMode=False
        if self.localdb:
            self.localdb.stop()
        self.localdb=DB(filename)
        d=self.localdb.getKeys()
        d.addCallback(self.updateKeys)

    def updateKeys(self,keys):
        self.statKeys={}
        for stat in keys:
            if not stat[0] in self.statKeys:
                self.statKeys[stat[0]]={}
            if not stat[1] in self.statKeys[stat[0]]:
                self.statKeys[stat[0]][stat[1]]={}
            self.statKeys[stat[0]][stat[1]][stat[2]]={}
        self.initStats()

    def retFileValues(self,stats,pid):
        for k,v in stats.items():
            self.plots[pid][k]=v

        for v in self.plots[pid].values():
            if v==-1:
                return

        data={}
        for k,v in self.plots[pid].items():
            if k!='plot':
                data[k]=v
        self.plots[pid]['plot'].updatePlots(data)


    def on_saveTButton_clicked(self,widget):
        if not self.statinGraph:
            return

        sharedx=self.sharedButton.get_active()

        newGraph={}
        for k,v in self.newGraph.items():
            newGraph[k]={}
            newGraph[k]['name']=v['name'].get_text()
            newGraph[k]['x']=v['x'].get_active_text()
            try:
                newGraph[k]['stats']=v['stats']
            except:
                newGraph[k]['stats']=self.newSubGraph


        saveDict={}
        saveDict['sharedx']=sharedx
        saveDict['graph']=newGraph

        self.browseSaveLocal(saveDict)

    def browseSaveLocal(self,saveDict):
        filter=gtk.FileFilter()
        filter.set_name('template files')
        filter.add_pattern('*.tmpl')

        dialog = gtk.FileChooserDialog("Open..",
                               None,
                               gtk.FILE_CHOOSER_ACTION_SAVE,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_SAVE, gtk.RESPONSE_OK))
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
        dialog.destroy()
        if filename and '.' not in os.path.basename(filename):
            filename+='.tmpl'

        self.saveTemplateFile(filename,saveDict)

    def saveTemplateFile(self,filename,saveDict):
        if not filename:
            return
        f=open(filename,'wb')
        dump(saveDict,f)
        f.close()

    def on_loadTButton_clicked(self,widget):
        for sub in widget.get_children():
            widget.remove(sub)

        directory=os.path.join(get_user_data_dir(),'stats')
        files=[f[:-5] for f in os.listdir(directory) if '.tmpl' in f]
        for f in files:
            l=gtk.MenuItem(f)
            l.show()
            l.connect('activate',self.loadFile,f)
            widget.append(l)

    def loadFile(self,widget,filename):
        if self.statinGraph:
            print "can't load templeta while making grph"
            return

        filename+='.tmpl'
        directory=os.path.join(get_user_data_dir(),'stats')
        filename=os.path.join(directory,filename)
        f=open(filename,'rb')
        graph=load(f)
        f.close()
        self.makeTemplateGraph(graph)

    def makeTemplateGraph(self,graph):
        sharedx=graph['sharedx']
        newGraph=graph['graph']

        if self.liveMode:
            self.getStatKeys()

        self.on_newButton_clicked(self.builder.get_object('newButton'))
        self.sharedButton.set_active(sharedx)
        for sub in newGraph.values():
            self.on_sub_clicked(None)
            self.newGraph[self.subCount]['name'].set_text(sub['name'])
            for x,pos in (('customX',0),('lpb',1),('time',2)):
                if sub['x']==x:
                    self.newGraph[self.subCount]['x'].set_active(pos)
            for stat in sub['stats']:
                comp=None
                sid=None
                name=None
                if stat[0] in self.statKeys:
                    comp=stat[0]
                    if stat[1] in self.statKeys[comp]:
                        sid=stat[1]
                    else:
                        sid=self.statKeys[comp].keys()[0]
                    if stat[2] in self.statKeys[comp][sid]:
                        name=stat[2]
                    else:
                        name=None
                else:
                    name=None

                if name:
                    if not self.statinGraph:
                        self.statinGraph=True
                    self.newSubGraph.append((comp,sid,name))
                    self.lStore.append((name,))







if __name__=='__main__':
    statsGui()
    reactor.run()



