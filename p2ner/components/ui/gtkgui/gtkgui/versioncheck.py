from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except:
    pass
from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from twisted.web.client import getPage
import xml.dom.minidom
from distutils.version import StrictVersion
import p2ner

VERSION=p2ner.__version__

def displayMessage(msg):
        error_dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO
                    , message_format=msg
                    , buttons=gtk.BUTTONS_OK)
        error_dlg.run()
        error_dlg.destroy()
        
def getText(nodelist):
    nodelist=nodelist.childNodes
    rc=[]
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def compareVersion(entry):
    v=entry.split('=')[-1]
    print 'page version:',v
    print 'my version:',VERSION
    if StrictVersion(v)>StrictVersion(VERSION):
        print 'should update'
        msg='There is an updated version of P2ner\n'
        msg +='You can download version '+str(v)+' from http://upg.iamnothere.org:8181/projects/p-2ner/files'
        displayMessage(msg)
    else:
        print 'you are good'
    
    
def readPage(page):
    dom = xml.dom.minidom.parseString(page)
    for ch in dom.getElementsByTagName('entry'):
        entry=getText(ch.getElementsByTagName('title')[0])
        if entry.split()[0].lower()=='executable':
            compareVersion(entry)
            return
        

def err(error):
    print error

def getVersion():
    page='http://upg.iamnothere.org:8181/projects/p-2ner/news.atom'
    d=getPage(page)
    d.addCallback(readPage)
    d.addErrback(err)
    

if __name__=='__main__':
    getVersion()
    reactor.run()