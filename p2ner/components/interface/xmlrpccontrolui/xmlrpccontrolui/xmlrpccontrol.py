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
from p2ner.core.components import getComponentsInterfaces as getCompInt
from p2ner.base.Stream import Stream
from p2ner.util.interfacelog import DatabaseLog
import os,os.path,stat,time
from random import uniform
from twisted.internet.threads import deferToThread
from p2ner.util.utilities import findNextTCPPort
from twisted.web.xmlrpc import Proxy

class xmlrpcControl(Interface,xmlrpc.XMLRPC):
    
    def initInterface(self,*args,**kwargs):
        xmlrpc.XMLRPC.__init__(self)
        self.dContactServers={}
        self.dSubStream={}
        self.dStopProducing={}
        self.dUnregisterStream={}
        self.dRegisterStream={}
        if 'vizir' in kwargs.keys() and kwargs['vizir']:
            print 'should register to ',kwargs['vizirIP'],kwargs['vizirPort']
            url="http://"+kwargs['vizirIP']+':'+str(kwargs['vizirPort'])+"/XMLRPC"
            self.proxy=Proxy(url)
        else:
            self.proxy=None
            
    def start(self):
        self.logger=DatabaseLog(_parent=self)
        print 'start listening xmlrpc'
        p=findNextTCPPort(9090)
        print p
        reactor.listenTCP(p, server.Site(self))
        if self.proxy:
            self.getIp(p)
       
    def getIp(self,port):
        try:   
            if self.basic:
                ip=self.netChecker.localIp
                p=self.root.controlPipe.getElement(name="UDPPortElement").port
                bw=self.root.trafficPipe.getElement(name="BandwidthElement").bw
            else:
                ip=self.netChecker.externalIp
                if self.netChecker.upnp: 
                    p=self.netChecker.upnpControlPort
                else:
                    p=self.netChecker.extControlPort
                bw=self.root.trafficPipe.getElement(name="BandwidthElement").bw
        except KeyError:
            reactor.callLater(1,self.getIp,port)
            return

        print ip,port,p,bw
        self.register(ip,port,p,bw)

    def register(self,ip,rpcport,port,bw):
        self.proxy.callRemote('register',ip,rpcport,port,bw)
        
    def xmlrpc_connect(self):
        return True

    def cleanUp(self):
        pass
        
    def xmlrpc_registerStream(self,stream,input=None,output=None):
        print 'trying to register stream'
        s=loads(stream)
        strm=Stream(**s)
        d=defer.Deferred()
        if input:
            input=loads(input)
        if output:
            output=loads(output)

        self.dRegisterStream[strm.streamHash()]=d
        self.root.registerStream(strm,input,output)        
        return d
    
    def xmlrpc_contactServer(self,server):
        print 'should contact:',server
        d=defer.Deferred()
        self.root.contactServers(server)
        self.dContactServers[tuple(server)]=d
        return d
    
    def xmlrpc_getProducingStreams(self):
        pStreams=self.root.getProducingStreams()
        s=[dumps(s) for s in pStreams]
        return s
    
    def xmlrpc_getRegisteredStreams(self):
        rStreams=self.root.getRegisteredStreams()
        r=[dumps(r) for r in rStreams]
        return r
    
    def xmlrpc_startProducing(self,id):
        self.root.startProducing(id)
        return True
    
    def xmlrpc_startRemoteProducer(self,id):
        self.root.startRemoteProducer(id)
        return True
    
    def xmlrpc_subscribeStream(self,id,ip,port,output=None):
        d=defer.Deferred()
        if not self.dSubStream.has_key(id):
            self.dSubStream[id]=d
        self.root.subscribeStream(id,ip,port,loads(output))
        return d
    
    def xmlrpc_stopProducing(self,id,changeRepub=False):
        d=defer.Deferred()
        if not self.dStopProducing.has_key(id):
            self.dStopProducing[id]=d
        self.root.stopProducing(id,changeRepub)
        return d
    
    def xmlrpc_unregisterStream(self,id):
        d=defer.Deferred()
        if not self.dUnregisterStream.has_key(id):
            self.dUnregisterStream[id]=d
        self.root.unregisterStream(id)
        return d
    
    def xmlrpc_quiting(self):
        reactor.callLater(0,self.root.quiting)
        return True
    
    def returnSubStream(self,stream,id):
        if stream!=-1:
            stream=dumps(stream)
        defer=self.dSubStream.pop(id)
        defer.callback((stream,id))
            

    def returnStopProducing(self,id):
        try:
            defer=self.dStopProducing.pop(id)
        except:
            return
        defer.callback(id)
            
    def returnUnregisterStream(self,id):
        defer=self.dUnregisterStream.pop(id)
        defer.callback(id)
            
    def returnProducedStream(self,stream,hash):
        try:
            d=self.dRegisterStream.pop(hash)
        except:
            return
        
        if stream!=-1:
            stream=dumps(stream)
        d.callback(stream)
           
    def returnContents(self,stream,server):
        d=stream    
        if stream!=-1:
            d=[dumps(s) for s in stream]
        defer=self.dContactServers.pop(server)
        defer.callback((d,server))
        
    def logRecord(self,record):
        if record.levelno%10==0:
            reactor.callLater(0,self.logger.addRecord,record)
        
    def xmlrpc_getRecords(self):
        ret=self.logger.getRecords()
        if ret:
            ret=[dict(r) for r in ret]
            ret= [dumps(r) for r in ret]
        else:
            ret=[]
        return ret
    
    def xmlrpc_requestFiles(self,dname):
        if not dname:
            dname = os.path.expanduser("~")
        #else:
        #   dname = os.path.abspath(dname)
        
        files=[]
        fl=['..']+os.listdir(dname)
        for f in fl:
            try:
                dot=f[1]
            except:
                dot=1
            rf=os.path.join(dname,f)
            if f[0]<>'.':
                filestat=os.stat(rf)
                files.append((f,stat.S_ISDIR(filestat.st_mode),filestat.st_size,time.ctime(filestat.st_mtime),oct(stat.S_IMODE(filestat.st_mode)),os.path.join(dname,f)))
            if f[0]=='.' and dot=='.':
                filestat=os.stat(rf)
                files.append((f,stat.S_ISDIR(filestat.st_mode),filestat.st_size,time.ctime(filestat.st_mtime),oct(stat.S_IMODE(filestat.st_mode)),os.path.join(dname,f)))

        return [dumps(f) for f in files]
    
    def networkUnreachable(self):
        print 'network conditions are not valid'
        
    def xmlrpc_getComponentsInterfaces(self,comp):
        c=getCompInt(comp)
        c=dumps(c)
        return (comp,c)
        
    def xmlrpc_copyConfig(self):
        filename,chFilename=self.preferences.getConfigFiles()
        f=open(filename,'rb')
        b=f.readlines()
        f.close()
        f=open(chFilename,'rb')
        r=f.readlines()
        f.close()
        if not r:
            r=-1
        return (b,r)
    
    def xmlrpc_saveRemoteConfig(self,file,chFile):
        self.preferences.saveFromRemoteConfig(file,chFile)
        return 0

    def xmlrpc_startConverting(self,dir,filename,videorate,subs,subsFile,subsEnc):
        id=self.root.startConverting(dir,filename,videorate,subs,subsFile,subsEnc)
        return id
    
    def xmlrpc_getConverterStatus(self,id):
        status=self.root.converters[id].getStatus()
        return status
        
    def xmlrpc_abortConverter(self,id):
        converter=self.root.converters.pop(id)
        converter.abort()
        return 0
    
    def xmlrpc_getStatistics(self):
        return self.stats.keys()
    
    def xmlrpc_getStatValues(self,stats):
        ret=[]
        for s,c in stats:
            count=self.stats[s]['count']
            if count>100:
                c=100 -( count - c)
            v=self.stats[s]['values'][c:]
            
            ret.append((s,v,count))
        return ret
    
    def xmlrpc_startBWMeasurement(self,ip):
        d=defer.Deferred()
        self.root.startBWMeasurement(ip,None,d)
        return d
    
    def xmlrpc_setBW(self,bw):
        self.root.setBW(bw)
        return 1
  
    def xmlrpc_getBW(self):
        return self.root.trafficPipe.getElement(name="BandwidthElement").bw


    def networkStatus(self,status):
        pass
    
    def networkUnreachable(self,status):
        self.root.exiting()
    
    def checkNetwork(self):
        reactor.callLater(0.2,self.netChecker.check)
       
    def xmlrpc_getNeighbours(self,id):
        strm=self.root.getStream(id)
        neighs=strm['overlay'].getNeighbours()
        ret=[dumps(p) for p in neighs]
        en=strm['overlay'].getEnergy()
        stats=strm['overlay'].getVizirStats()
        return (ret,en,stats)
    
   