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

from p2ner.abstract.interface import Interface
from twisted.web import xmlrpc, server
from twisted.internet import reactor,defer
from cPickle import dumps,loads
from p2ner.util.utilities import findNextTCPPort,getIP
from twisted.web.xmlrpc import Proxy
from p2ner.util.interfacelog import DatabaseLog

class xmlrpcControl(Interface,xmlrpc.XMLRPC):

    def initInterface(self,*args,**kwargs):
        xmlrpc.XMLRPC.__init__(self)
        self.logger=DatabaseLog(_parent=self,server=True)
        print 'should register to ',kwargs['vizirIP'],kwargs['vizirPort']
        url="http://"+kwargs['vizirIP']+':'+str(kwargs['vizirPort'])+"/XMLRPC"
        self.vip=kwargs['vizirIP']
        self.vport=kwargs['vizirPort']
        self.proxy=Proxy(url)


    def start(self):
        print 'start listening xmlrpc'
        p=findNextTCPPort(9090)
        print p
        reactor.listenTCP(p, server.Site(self))
        self.register(getIP(self.vip,self.vport)[0], p)


    def register(self,ip,port):
        try:
            p=self.root.controlPipe.callSimple('getPort')
        except:
            reactor.callLater(0.5,self.register,ip,port)
            return

        self.proxy.callRemote('register',ip,port,p,0,True)

    def xmlrpc_restartServer(self):
        print 'restarting server'
        self.root.restartServer()
        return 1

    def logRecord(self,record):
         self.logger.addRecord(record)

    def xmlrpc_getRecords(self):
        d=self.logger.getRecords()
        d.addCallback(self.dumpRecords)
        return d

    def dumpRecords(self,ret):
        if ret:
            ret=[dict(r) for r in ret]
            ret= [dumps(r) for r in ret]
        else:
            ret=[]
        return ret

