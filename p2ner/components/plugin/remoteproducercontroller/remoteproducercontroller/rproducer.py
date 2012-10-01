from p2ner.abstract.interface import Interface
from twisted.web import xmlrpc, server
from twisted.internet import reactor,defer
from cPickle import dumps,loads
from p2ner.base.Stream import Stream
import p2ner.util.config as config
from random import uniform
from hashlib import md5
from p2ner.util.config import get_channels,getRemotePreferences
from p2ner.util.utilities import findNextTCPPort
import os,os.path

class RemoteProducerInterface(Interface,xmlrpc.XMLRPC):
    
    def initInterface(self):
        xmlrpc.XMLRPC.__init__(self)
        self.dContactServers={}
        pref=getRemotePreferences()
        
        if not pref['enable']:
            return
        
        print 'start listening xmlrpc remote producer'
        p=findNextTCPPort(9290)
        print p
        self.pd=None
        self.password=pref['password']
        self.dir=pref['dir']
        reactor.listenTCP(p, server.Site(self))
        
    def xmlrpc_connect(self,password):
        print 'got passworddddddd ',password
        #m=md5()
        #m.update(self.password)
        #passwrd=m.hexdigest()
        if password==self.password:
            return 1
        else:
            return 0
        
    def xmlrpc_getContents(self):
        self.channels=get_channels()
        videos=os.listdir(self.dir)
        return videos,self.channels.keys()
    
    def xmlrpc_registerStream(self,stream,input=None,output=None):
        if self.pd:
            return -1
        print 'trying to register stream'
        s=loads(stream)

        strm=Stream(**s)
        if strm.type=='tv':
            strm.filename=(self.channels[strm.filename]['location'],self.channels[strm.filename]['program'])
        else:
            strm.filename=os.path.join(self.dir,strm.filename)
        self.pd=defer.Deferred()
        if input:
            input=loads(input)
        if output:
            output=loads(output)
            
        for s in self.root.getProducingStreams():
            self.root.stopProducing(s.id,True)
        self.root.registerStream(strm,input,output)     
        reactor.callLater(1,self.waitStream)
        self.waitCount=1
        return self.pd
    
    def waitStream(self):
        if not self.root.getProducingStreams():
            if self.waitCount<5:
                reactor.callLater(1,self.waitStream)
                self.waitCount +=1
            else:
                self.pd.callback(-2)
                self.pd=None
        else:
            stream=self.root.getProducingStreams()[0]
            self.root.startProducing(stream.id)
            self.pd.callback(stream.id)
            self.pd=None