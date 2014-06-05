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
import sys

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
                # p=self.root.controlPipe.getElement(name="UDPPortElement").port
                p=self.root.controlPipe.callSimple('getPort')
                bw=self.root.trafficPipe.callSimple('getBW')
            else:
                ip=self.netChecker.externalIp
                if self.netChecker.upnp:
                    p=self.netChecker.upnpControlPort
                else:
                    p=self.netChecker.extControlPort
                bw=self.root.trafficPipe.callSimple('getBW')
        except KeyError:
            reactor.callLater(1,self.getIp,port)
            return

        print ip,port,p,bw
        self.pip=ip
        self.pport=p
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
        print 'should stop producing stream :',id
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
        if type(defer)!=list:
            defer.callback((stream,id))
        else:
            defer[0].callback(id)


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

        if type(d)!=list:
            if stream!=-1:
                stream=dumps(stream)
            d.callback(stream)
        else:
            self.root.startProducing(stream.id)
            d[0].callback(stream.id)


    def returnContents(self,stream,server):
        defer=self.dContactServers.pop(server)
        if type(defer)!=list:
            d=stream
            if stream!=-1:
                d=[dumps(s) for s in stream]
            defer.callback((d,server))
        else:
            defer=defer[0]
            if stream!=-1:
                d=[(s.id,s.title,s.author,s.description) for s in stream]
            defer.callback(d)

    def logRecord(self,record):
        if record.levelno%10==0:
            self.logger.addRecord(record)
        if record.levelno==40:
            msg=record.getMessage()
            sys.stderr.write(msg+'\n')
            if self.proxy:
                self.proxy.callRemote('logerror',self.pip,self.pport,msg)

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
        return self.root.trafficPipe.callSimple('getBW')


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

    def xmlrpc_stopSwapping(self,stop,id):
        strm=self.root.getStream(id)
        strm['overlay'].toggleSwap(stop)
        return 1


    def xmlrpc_registerSteerStream(self,title,author,desc,port,trackerIP,trackerPort):
        print 'trying to register stream'
        s={}
        s['overlay']={'numNeigh': 8, 'component': 'DistributedClient', 'swapFreq': 3}
        s['server']=(trackerIP,trackerPort)
        s['scheduler']= {'blocksec': 7, 'bufsize': 30, 'component': 'PullClient', 'reqInt': 2}
        s['password']=None
        s['republish']=False
        s['startable']=False
        s['startTime']=0
        s['type']='stream'
        s['description']=desc
        s['author']=author
        s['title']=title
        s['filename']='rtp//@:'+str(port)

        input= {'videoRate': 0, 'component': 'GstInput', 'advanced': False}
        output={'comp': 'NullOutput', 'kwargs': {}}

        strm=Stream(**s)
        d=defer.Deferred()

        self.dRegisterStream[strm.streamHash()]=[d]
        self.root.registerStream(strm,input,output)
        return d


    def xmlrpc_contactSteerServer(self,trackerIP,trackerPort):
        server=(trackerIP,trackerPort)
        print 'should contact:',server
        d=defer.Deferred()
        self.root.contactServers(server)
        self.dContactServers[tuple(server)]=[d]
        return d

    def xmlrpc_subscribeSteerStream(self,id,trackerIP,trackerPort,output,gstPort):
        d=defer.Deferred()
        if not output:
            output={'comp': 'NullOutput', 'kwargs': {}}
        elif output==1:
            output={'comp': 'GstOutput', 'kwargs': {'port': {'value':gstPort}}}
        else:
            output={'comp': 'PureVlcOutput', 'kwargs': {}}




        if not self.dSubStream.has_key(id):
            self.dSubStream[id]=[d]
        self.root.subscribeStream(id,trackerIP,trackerPort,output)
        return d


    def xmlrpc_getStats(self,sid):
        ret={}
        cbw=self.root.controlPipe.callSimple('getStats')
        ret[-1]={}
        ret[-1]['controrBW']=cbw[0][2]
        s=self.root.getStream(sid)
        st=s['overlay'].getStats()
        for s in st:
            if s[0] not in ret:
                ret[s[0]]={}
            ret[s[0]][s[1]]=s[2]
        return dumps(ret)


