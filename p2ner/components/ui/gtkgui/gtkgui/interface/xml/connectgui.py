import os, sys
from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from twisted.web.xmlrpc import Proxy

class ConnectGui(object):
    
    def __init__(self,parent):
        self.parent=parent
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'connect.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'connect.glade'))
            
        self.builder.connect_signals(self)
        
        self.statusbar = self.builder.get_object("statusbar")
        self.context_id = self.statusbar.get_context_id("Statusbar")
        
        self.ui = self.builder.get_object("ui")
        self.ui.show()
        
    def on_connectButton_clicked(self,widget):
        ip=self.builder.get_object('ipEntry').get_text()
        port=self.builder.get_object('portEntry').get_text()
        self.url="http://"+ip+':'+port+"/XMLRPC"
        print self.url
        proxy = Proxy(self.url)
        d =proxy.callRemote('connect')
        d.addCallback(self.succesfulConnection)
        d.addErrback(self.failedConnection)
        
    def succesfulConnection(self,d):
        self.parent.interface.setUrl(self.url)
        self.parent.startUI()
        self.ui.destroy()
        
    def failedConnection(self,f):
        self.statusbar.push(self.context_id, "Can't connect to server")
        print f
    def on_exitButton_clicked(self,widget):
        self.ui.destroy()
	self.root.quit()
        reactor.stop()
