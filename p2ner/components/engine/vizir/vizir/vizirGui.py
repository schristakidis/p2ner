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
pygtk.require("2.0")
import gtk
import gobject
try:
    from twisted.web.xmlrpc import Proxy,withRequest
except:
    pass
from cPickle import dumps,loads
from twisted.web import xmlrpc, server
from twisted.internet import reactor,defer
from twisted.internet import task
from producer import PGui
from p2ner.abstract.ui import UI
from client import PClient
from util import getText,getChoice
from pkg_resources import resource_string
from p2ner.core.components import loadComponent


OFF=0
ON=1
INPROGRESS=2
PAUSE=3


class vizirGui(UI,xmlrpc.XMLRPC):
    def initUI(self,port=9000):
        xmlrpc.XMLRPC.__init__(self)
        print 'start listening xmlrpc'
        reactor.listenTCP(port, server.Site(self))
        self.proxy=None
        self.remote=True

        self.vizInterface = loadComponent('plugin', 'VizXMLInterface')(_parent=self)
        self.vizPlot= loadComponent('plugin', 'OverlayViz')() 
        self.overlayShowing=False

        self.constructGui()
            
    def constructGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'cc.glade'))
        self.win = self.builder.get_object("controlcenter")
        self.treeview = self.builder.get_object("clientView")
        self.treemodel = None

        startNclients = self.builder.get_object("startNclients")
        stopNclients = self.builder.get_object("stopNclients")
        setUploadBW = self.builder.get_object("setUploadBW")
        startProducer = self.builder.get_object("startProducer")
        showOverlay = self.builder.get_object("showOverlay")
        startNclients.connect("clicked", self.startNclients)
        stopNclients.connect("clicked", self.stopNclients)
        setUploadBW.connect("clicked", self.setUploadBW)
        startProducer.connect("clicked", self.startProducing)
        showOverlay.connect("clicked", self.showOverlay)
        self.win.set_title("VizEW - Control Center")
        pixbuf = self.win.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_MENU)
        self.win.set_icon(pixbuf)
        self.formatview()
        self.treeview.connect('button-press-event', self.on_buttonpress, self.treemodel)
        self.bar=self.builder.get_object('statusbar1')
        self.context_id=self.bar.get_context_id('status bar')
        self.win.connect('destroy',self.on_win_destroy)
        self.win.show_all()
        
    def on_win_destroy(self,*args):
        reactor.stop()
        
    def formatview(self):
        self.treemodel = gtk.ListStore(str, int, str, int, str, int, gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT) #(ip,port,bw,status,type,proxyport, id,object)
        self.treeview.set_model(self.treemodel)
        self.treemodel.set_default_sort_func(self.sort_func)
        self.treemodel.set_sort_column_id(-1,gtk.SORT_ASCENDING)
        
        cell = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn("On", cell)
        col.set_cell_data_func(cell, self.ison_pixbuf)
        self.treeview.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn("Host", gtk.CellRendererText(), text=0)
        self.treeview.append_column(col)
        col = gtk.TreeViewColumn("Port", gtk.CellRendererText(), text=1)
        self.treeview.append_column(col)
        col = gtk.TreeViewColumn("Upload BW", gtk.CellRendererText(), text=2)
        self.treeview.append_column(col)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        self.clientStore=gtk.ListStore(str)
        for t in ('client','producer'):
            self.clientStore.append([t])
  
        self.serverStore=gtk.ListStore(str)
        self.serverStore.append(['server'])
        
        cell=gtk.CellRendererCombo()
        cell.set_property("editable", True)
        cell.set_property('has_entry',False)
        cell.set_property("text-column", 0)
        cell.connect("edited", self.combo_changed)
          
        col = gtk.TreeViewColumn("Type", cell, text=4)
        col.set_cell_data_func(cell,self.setCellModel)
        self.treeview.append_column(col)
        
 
    def sort_func(self,model,iter1,iter2,data=None):
        t1=model.get_value(iter1,4)
        t2=model.get_value(iter2,4)
        if t1==t2:
            return 0
        elif t1>t2:
            return -1
        else:
            return 1
        
    @withRequest
    def xmlrpc_registerProxy(self,request,port):
        print 'using proxy'
        url="http://"+request.getClientIP()+':'+str(port)+"/XMLRPC"
        self.proxy=Proxy(url)
        return True
    
    def xmlrpc_register(self,ip,rpcport,port,bw,server=False):
        if server:
            type='server'
            on=ON
            id=[]
        else:
            type='client'
            on=OFF
            id=-1
        bw='%.2f'%(bw/1024)
        peer=(ip,rpcport)
        o=PClient(self,peer,_parent=self)
        self.treemodel.append((ip,port,bw,on,type,rpcport,id,o))
        return True
    
    def combo_changed(self, widget, path, text):
        if self.treemodel[path][3]==OFF :
            self.treemodel[path][4] = text
        else:
            self.newStatusMessage("can't change the type of a client if it's not OFF")
        
    def setCellModel(self,col,cell,model,iter):
        t=model.get_value(iter,4)
        if t!='server':
            m=self.clientStore
        else:
            m=self.serverStore
        cell.set_property('model',m)
        
    def ison_pixbuf(self, column, cell, model, iter):
        ison = model.get_value(iter, 3)
        if ison==ON:
            cell.set_property('stock-id', gtk.STOCK_YES)
        elif ison==OFF:
            cell.set_property('stock-id', gtk.STOCK_NO)
        elif ison==INPROGRESS:
            cell.set_property('stock-id', gtk.STOCK_EXECUTE)
        elif ison==PAUSE:
            cell.set_property('stock-id', gtk.STOCK_MEDIA_PAUSE)
        return

    def on_buttonpress(self, widget, event, model):
        try:
            (path, column, x, y) = widget.get_path_at_pos(int(event.x), int(event.y))
            iter = model.get_iter(path)
        except: 
            return
        #send start stop
        if( widget.get_column(0) == column and event.button != 3):
            self.toggleStartStop(iter)
        #pup up context menu
        elif( event.button == 3):
            ret=False
            if self.treemodel.get_path(iter) in [p for p in self.treeview.get_selection().get_selected_rows()[1]]:
                ret=True
            menu = self.popupMenu(event,iter,ret)
            menu.popup( None, None, None, event.button, event.time)
            return ret

    def getServers(self):
        servers=[(m[0],m[1]) for m in self.treemodel if m[4]=='server']
        ret={}
        for s in servers:
            if ret.has_key(s[0]):
                ret[s[0]].append(s[1])
            else:
                ret[s[0]]=[s[1]]
        return ret
    
    def toggleStartStop(self, iter, id=None):
        c=self.treemodel.get_value(iter,7)
        if self.treemodel.get_value(iter,4)=='producer':
            if self.treemodel.get_value(iter,3)==OFF:
                if len(self.getServers()):
                    peer=(self.treemodel.get_value(iter,0),self.treemodel.get_value(iter,5))
                    PGui(self,peer,_parent=self)
                else:
                    self.newStatusMessage("can't start producing without a server")
            elif self.treemodel.get_value(iter,3)==PAUSE:
                c.sendStartProducing(self.treemodel.get_value(iter,6),'produce')
                self.treemodel.set_value(iter,3,ON)
            elif self.treemodel.get_value(iter,3)==ON:
                c.sendStopProducing(self.treemodel.get_value(iter,6))
                self.treemodel.set_value(iter,3,INPROGRESS)
        elif self.treemodel.get_value(iter,4)=='client':
            if self.treemodel.get_value(iter,3)==OFF:
                if not id:
                    id=self.getProducingId()
                    if not id:
                        self.newStatusMessage('there is no available streams to subscribe')
                        return
                    elif len(id)==1:
                        id=id[0] 
                    else:
                        sid=int(getChoice('select which id to subscribe', [i[1] for i in id],None,None))
                        id=[i for i in id if i[1]==sid][0]
                output=c.getOutput()
                c.sendSubsribe(id[1],id[0][0],id[0][1],output)
                self.treemodel.set_value(iter,3,INPROGRESS)
            elif self.treemodel.get_value(iter,3)==ON:
                c.sendUnregisterStream(self.treemodel.get_value(iter,6))
                self.treemodel.set_value(iter,3,INPROGRESS)
        return

    def findPeer(self,peer,rpc=False):  
        ip=peer[0]
        port=int(peer[1])
        if rpc:
            p=1
        else:
            p=5
        peer=[m for m in self.treemodel if m[0]==ip and m[p]==port]
        if len(peer)!=1:
            print 'problem in self status find peer'
            print peer
            return None
        
        return peer[0]
       
    def setStatus(self,peer,status):
        p=self.findPeer(peer)
        if p:
            p[3]=status
        
    def setId(self,peer,id,rpc=False):
        p=self.findPeer(peer,rpc)
        if p and p[4]!='server':
            p[6]=id
        else:
            p[6].append(id)
                   
    def getProducingId(self):
        peer=[m for m in self.treemodel if m[4]=='producer' and m[6]!=-1]
        ret=[]
        for p in peer:
            id=p[6]
            server=self.getServerId(id)
            ret.append((server,id))
        return ret
    
    def getServerId(self,id):
        server=[m for m in self.treemodel if m[4]=='server' and id in m[6]]
        if len(server)==1:
            server=(server[0][0],server[0][1])
            return server
        else:
            raise ValueError('problem in getServerId in vizirGui')
        return None
    
    def producerStopped(self,id):
        clients=[m for m in self.treemodel if m[4]=='client' and m[6]==id]
        for c in clients:
            c[3]=OFF
        servers=[m for m in self.treemodel if m[4]=='server' and id in m[6]]
        if len(servers)==1:
            servers[0][6].remove(id)
        else:
            raise ValueError('problem in producer Stopped in vizirGui')
        
    def newStatusMessage(self,message):
        self.bar.pop(self.context_id)
        self.bar.push(self.context_id, message)

    def startNclients(self, args):
        id=self.getProducingId()
        if not id:
            self.newStatusMessage('there is no available streams to subscribe')
            return
        elif len(id)==1:
            id=id[0]
        else:
            sid=int(getChoice('select which id to subscribe', [i[1] for i in id],None,None))
            id=[i for i in id if i[1]==sid][0]
            
        clients = self.getAvailableClients()
        ret = getText("Clients:", "Insert number of clients to start:", "Maximum number is <b>%d</b>" % len(clients))
        try:
            num = int(ret)
        except:
            self.newStatusMessage('number of client to start should be an integer')
            return
        
        self._startNclients(num,id)
        
    def _startNclients(self, num ,id=None):
        iterator = self.treemodel.get_iter_first()
        while iterator:
            if num:
                if self.treemodel.get_value(iterator, 3)!=OFF or self.treemodel.get_value(iterator,4)!='client':
                    iterator = self.treemodel.iter_next(iterator)
                else:
                    reactor.callLater(num*0.5,self.toggleStartStop,iterator,id)
                    num -= 1
                    iterator = self.treemodel.iter_next(iterator)
            else:
                break
    
    def stopNclients(self, args):
        id=self.getProducingId()
        if not id:
            self.newStatusMessage('there is no streams running')
            return
        elif len(id)==1:
            id=id[0][1]
        else:
            sid=int(getChoice('select which id to stop clients', [i[1] for i in id],None,None))
            id=[i for i in id if i[1]==sid][0][1]
            
        clients = len(self.getRunningClients(id))

        ret = getText("Clients:", "Insert number of clients to stop:", "Maximum number is <b>%d</b>" % clients)
        try:
            num = int(ret)
        except:
            self.newStatusMessage('number of client to stop should be an integer')
            return
        
        self._stopNclients(num,id)
        
    def _stopNclients(self, num,id):
        iterator = self.treemodel.get_iter_first()
        while iterator:
            if num:
                if  self.treemodel.get_value(iterator, 3)!=ON or self.treemodel.get_value(iterator,4)!='client'  or self.treemodel.get_value(iterator,6)!=id:
                    iterator = self.treemodel.iter_next(iterator)
                else:
                    self.toggleStartStop(iterator)
                    num -= 1
                    iterator = self.treemodel.iter_next(iterator)
            else:
                break

    def getAvailableClients(self):
        return [m for m in self.treemodel if m[3]==OFF and m[4]=='client']

    def getRunningClients(self,id):
        return [m for m in self.treemodel if m[3]==ON and m[4]=='client' and m[6]==id]
    
    def popupMenu(self, event,iter,right=True):
        menu = gtk.Menu()
        if self.treemodel.get_value(iter,4)=='server':
            menuitems = {"Restart Server" : self.restartServer}
            iters=[iter]
        else:
            if right:
                selection = self.treeview.get_selection().get_selected_rows()
                iters=[self.treemodel.get_iter(path)  for path in selection[1] if self.treemodel.get_value(self.treemodel.get_iter(path),4)!='server']
            else:
                iters=[iter]
                
            outputMenu=gtk.Menu()
            
            menu_item=gtk.RadioMenuItem(None,'Null Output')
            menu_item.connect('toggled',self.on_output_menu_toggled,iters)
            menu_item.show()
            outputMenu.append(menu_item)
            
            menu_item1=gtk.RadioMenuItem(menu_item,'Vlc Output')
            menu_item1.connect('toggled',self.on_output_menu_toggled,iters)
            menu_item1.show()
            outputMenu.append(menu_item1)
            
            outputsItem=gtk.MenuItem('Select Output')
            outputsItem.set_submenu(outputMenu)
            menu.append(outputsItem)
            
            menuitems = {"Set UploadBW" : self._setUploadBW}
            
                
        for i in menuitems.keys():
            menu_item = gtk.MenuItem(i)
            menu_item.connect("activate", menuitems[i], iters)
            menu.append(menu_item)
        menu.show_all()
        return menu
    
    def on_output_menu_toggled(self,widget,iters):
        name=widget.get_label()
        for iterator in iters:
            c = self.treemodel.get_value(iterator, 7)
            c.setOutput(name)
        
        
    def setUploadBW(self,widget):
        selection = self.treeview.get_selection().get_selected_rows()
        iters=[self.treemodel.get_iter(path)  for path in selection[1] if self.treemodel.get_value(self.treemodel.get_iter(path),4)!='server']
        if iters:
            self._setUploadBW(widget, iters)
            
    def _setUploadBW(self, args, iters):
        bw = getText("", "Upload bandwidth", "Insert new upload bandwidth:")
        try:
            bw=float(bw)
        except:
            self.newStatusMessage('bandwidth must be a double')
            return
        for iterator in iters:
            c = self.treemodel.get_value(iterator, 7)
            c.sendNewBW(bw)
            
    def setBW(self,peer,bw):
        p=self.findPeer(peer)
        if p:
            p[2]='%.2f'%(bw/1024)
        
    def restartServer(self,args,iters):
        iter=iters[0]
        c=self.treemodel.get_value(iter,7)
        c.restartServer()
        
    def startProducing(self,widget):
        producers=[]
        iterator = self.treemodel.get_iter_first()
        while iterator:
            if self.treemodel.get_value(iterator,4)=='producer':
                producers.append(iterator)
            iterator = self.treemodel.iter_next(iterator)

        if not producers:
            self.newStatusMessage('there are no producers')
            return 
        if len(producers)==1:
            self.toggleStartStop(producers[0])
        else:
            prod=[p for p in producers if self.treemodel.get_value(p,3)==PAUSE]
            if not prod:
                self.toggleStartStop(producers[0])
            elif len(prod)==1:
                self.toggleStartStop(prod[0])
            else:
                id=self.getProducingId()
                sid=int(getChoice('select producer to start', [i[1] for i in id],None,None))
                prod=[p for p in prod if self.treemodel.get_value(p,6)==sid]
                self.toggleStartStop(prod[0])
                
    def showOverlay(self,widget):
        if self.overlayShowing:
            self.vizPlot.stop()
            self.overlayShowing = not self.overlayShowing
            return
        
        id=self.getProducingId()
        if not id:
            self.newStatusMessage('there is no available overlays to plot')
            return
        elif len(id)==1:
            id=id[0][1]
        else:
            sid=int(getChoice('select which id to plot', [i[1] for i in id],None,None))
            id=[i for i in id if i[1]==sid][0][1]
        self.vizInterface.setId(id)
        self.vizPlot.start(self.vizInterface)
        self.overlayShowing = not self.overlayShowing
            
        
        
    def getPeers(self):
        return [m[7] for m in self.treemodel if m[3]==ON and m[4]=='client' and m[6]==id]
                
def startVizirGui():
    from twisted.internet import reactor
    import sys,getopt
    try:
        optlist,args=getopt.getopt(sys.argv[1:],'p:h',['port=','help'])
    except getopt.GetoptError as err:
        usage(err=err)
        
    port=9000
    plot=False
    
    for opt,a in optlist:
        if opt in ('-p','--port'):
            port=int(a)
        elif opt in ('-h','--help'):
            usage()
 
    vizirGui(port)
    reactor.run()
    
def usage(err=None,daemon=False):
    import sys
    if err:
        print str(err)
    print ' -------------------------------------------------------------------------'
    print ' Run P2ner Vizir'
    print ' '
    print ' -p, --port port :define port'
    print ' -g, --graph :enable overlay visualization'
    print ' -h, --help :print help'
    print ' -------------------------------------------------------------------------'
    sys.exit(' ')
    
if __name__=='__main__':
    startVizirGui()
    