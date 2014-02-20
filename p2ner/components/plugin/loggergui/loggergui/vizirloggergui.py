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

import os.path,sys
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from twisted.internet import task,reactor
from pkg_resources import resource_string
from p2ner.abstract.ui import UI
from loggergui import LoggerGui
from vizirdb import DatabaseLog

levels = {
    "info": 1,
    "warning": 2,
    "error": 3,
    "critical": 4,
    "debug": 0
}

levelColors = {
               'info':'blue',
               'error':'red',
               'warning':'orange',
               'critical':'red'
               }

class VizirLoggerGui(LoggerGui):

    def start(self,widget):
        self.local=False
        if not self.ui:
            self.db=DatabaseLog(_parent=self)
            self.createGui()
            self.createSidePane()
        if not self.showing:
            self.ui.show()
            self.showing=True

    def createSidePane(self):
        self.sidePane=self.builder.get_object('sidePane')
        self.builder.get_object('pauseButton').set_sensitive(False)

        self.peerView=self.builder.get_object('peerView')

        self.peerStore=gtk.ListStore(str,int,bool,bool,str)
        self.peerView.set_model(self.peerStore)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('Peer',renderer, text=0 , background=4)
        self.peerView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('Port',renderer, text=1, background=4)
        self.peerView.append_column(column)

        renderer=gtk.CellRendererToggle()
        column=gtk.TreeViewColumn("showing",renderer, active=2)
        renderer.connect("toggled", self.showing_toggled_cb, self.peerStore)
        #renderer.set_sensitive(False)
        #renderer.set_activatable(False)
        self.peerView.append_column(column)

        renderer=gtk.CellRendererToggle()
        column=gtk.TreeViewColumn("logs",renderer, active=3)
        renderer.connect("toggled", self.logs_toggled_cb, self.peerStore)
        self.peerView.append_column(column)

        self.peerView.connect('button-press-event', self.on_buttonpress, self.peerStore)

        filter=self.builder.get_object('filterButton')
        filter.connect('toggled',self.on_filterButton_toggled)
        filter.set_visible(True)
        filter.set_active(True)

        refreshButton=self.builder.get_object('refreshButton')
        refreshButton.connect('clicked',self.on_refreshButton_clicked)

    def on_refreshButton_clicked(self,widget):
        peers=self.root.getPeers()
        avPeers=[(m[0],m[1]) for m in self.peerStore]
        for peer in peers:
            if peer not in avPeers:
                self.peerStore.append((peer[0],peer[1],False,False,'white'))

    def showing_toggled_cb(self,cell,path,model):
        if not model.get_value(model.get_iter(path),3):
            return

        model.set_value(model.get_iter(path),2,not model.get_value(model.get_iter(path),2))
        if model.get_value(model.get_iter(path),2):
            self.filters['peer'].append((model.get_value(model.get_iter(path),0),model.get_value(model.get_iter(path),1)))
        else:
            self.filters['peer'].remove((model.get_value(model.get_iter(path),0),model.get_value(model.get_iter(path),1)))
        self.tfilter.refilter()

    def logs_toggled_cb(self,cell,path,model):
        if model.get_value(model.get_iter(path),3):
            return
        else:
            ip=model.get_value(model.get_iter(path),0)
            port=model[path][1]
            peer=self.root.findPeerObject((ip,port))
            peer.getLog(self.newLog,ip,port)

        model.set_value(model.get_iter(path),3,not model.get_value(model.get_iter(path),3))

    def on_filterButton_toggled(self,widget):
        self.sidePane.set_visible(widget.get_active())
        self.ui.resize(1,1)

    def newLog(self,records,ip,port):
        print 'got records ', len(records)
        for m in self.peerStore:
            if m[0]==ip and m[1]==port:
                if not m[2]:
                    m[2]=True
                    self.filters['peer'].append((ip,port))
                    print self.filters['peer']
                    break

        d=self.db.addRecord(records)
        d.addCallback(self._getRecords)

    def _getRecords(self,d):
        d=self.db.getRecords()
        d.addCallback(self.clearView)
        d.addCallback(self.updateView)

    def clearView(self,records):
        self.tmodel.clear()
        self.tfilter=self.tmodel.filter_new()
        self.tfilter.set_visible_func(self.filterFunc)
        self.tview.set_model(self.tfilter)
        print 'in clear view ',len(records)
        return records

    def on_buttonpress(self, widget, event, model):
        try:
            (path, column, x, y) = widget.get_path_at_pos(int(event.x), int(event.y))
            iter = model.get_iter(path)
        except:
            return


        if( event.button == 3):
            if model.get_value(iter,3):
                menu = self.popupMenu(event,iter)
                menu.popup( None, None, None, event.button, event.time)
                return

    def popupMenu(self, event,iter):
        menu = gtk.Menu()
        menuItem=gtk.MenuItem('Refresh')
        menuItem.connect('activate',self.refreshLog,iter)
        menu.append(menuItem)

        menuItem=gtk.MenuItem('Set Color')
        menuItem.connect('activate',self.setColor,iter)
        menu.append(menuItem)
        menu.show_all()
        return menu

    def refreshLog(self,widget,iter):
        ip=self.peerStore.get_value(iter,0)
        port=self.peerStore.get_value(iter,1)
        peer=self.root.findPeerObject((ip,port))
        peer.getLog(self.newLog,ip,port)

    def setColor(self,widget,iter):
        colorseldlg=gtk.ColorSelectionDialog('Choose color...')
        colorsel = colorseldlg.colorsel

        response =colorseldlg.run()

        if response==gtk.RESPONSE_OK:
            color = colorsel.get_current_color()
            self.peerStore.set_value(iter,4,color)
            ip=self.peerStore.get_value(iter,0)
            port=self.peerStore.get_value(iter,1)
            for m in self.tmodel:
                if m[0]==ip and m[1]==port:
                    m[-1]=color
                    m[-2]=color
        colorseldlg.destroy()

