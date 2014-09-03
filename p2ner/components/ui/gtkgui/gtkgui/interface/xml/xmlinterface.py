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

from cPickle import loads,dumps
from twisted.web.xmlrpc import Proxy
from twisted.internet import reactor
from p2ner.abstract.interface import Interface

class Interface(Interface):
    def initInterface(self, *args, **kwargs):
        if args and args[0]:
            self.parent=args[0]
        else:
            self.parent=self.root

    def setUrl(self,url):
        self.proxy = Proxy(url)

    def getStreams(self):
        d = self.proxy.callRemote('getProducingStreams')
        d.addCallback(self.loadStreams)
        d.addCallback(self.parent.updateRegStreams)
        d.addErrback(self.failedXMLRPC)

        d = self.proxy.callRemote('getRegisteredStreams')
        d.addCallback(self.loadStreams)
        d.addCallback(self.parent.updateSubStreams)
        d.addErrback(self.failedXMLRPC)

    def loadStreams(self,streams):
        return [loads(s) for s in streams]

    def contactServers(self,servers):
        for s in servers:
            d = self.proxy.callRemote('contactServer',s)
            d.addCallback(self.returnContents)
            d.addErrback(self.failedXMLRPC)

    def returnContents(self,stream):
        streams=stream[0]
        server=stream[1]
        s=streams
        if streams!=-1:
            s=[loads(s) for s in streams]
        self.parent.getStream(s,server)

    def subscribeStream(self,id,ip,port,outputMethod):
        d = self.proxy.callRemote('subscribeStream',id,ip,port,dumps(outputMethod))
        d.addCallback(self.returnSubStream)
        d.addErrback(self.failedXMLRPC)

    def returnSubStream(self,stream):
        s=stream[0]
        id=stream[1]
        if s!=-1:
            s=loads(s)
        self.parent.succesfulSubscription(s,id)

    def returnPublishStream(self,stream):
        if stream!=-1:
            stream=loads(stream)
        self.parent.registerStream([stream])

    def stopProducing(self,id,repub):
        d = self.proxy.callRemote('stopProducing',id,repub)
        d.addCallback(self.parent.stopProducing)
        d.addErrback(self.failedXMLRPC)

    def unregisterStream(self,id):
        d=self.proxy.callRemote('unregisterStream',id)
        d.addCallback(self.parent.unregisterStream)
        d.addErrback(self.failedXMLRPC)

    def startProducing(self,id,type):
        d = self.proxy.callRemote('startProducing',id)
        #d.addCallback(self.parent.changeStreamStatus,id,type)
        d.addErrback(self.failedXMLRPC)

    def startRemoteProducer(self,id,type):
        d = self.proxy.callRemote('startRemoteProducer',id)
        #d.addCallback(self.parent.changeStreamStatus,id,type)
        d.addErrback(self.failedXMLRPC)

    def registerStream(self,settings,inputMethod,outputMethod):
        d = self.proxy.callRemote('registerStream', dumps(settings),dumps(inputMethod),dumps(outputMethod))
        d.addCallback(self.returnPublishStream)
        d.addErrback(self.failedXMLRPC)

    def quiting(self):
        d = self.proxy.callRemote('quiting')
        d.addCallback(self.quit)
        d.addErrback(self.quit)

    def quit(self,d):
        reactor.stop()


    def loadRecords(self,records):
        return [loads(r) for r in records]

    def requestFiles(self,rcom,arg,lcom):
        d=self.proxy.callRemote(rcom,arg)
        d.addCallback(self.loadRecords)
        d.addCallback(lcom)
        d.addErrback(self.failedXMLRPC)

    def getComponentsInterfaces(self,comp):
        d=self.proxy.callRemote('getComponentsInterfaces',comp)
        d.addCallback(self.loadComponents)
        d.addErrback(self.failedXMLRPC)

    def loadComponents(self,comp):
        interfaces=loads(comp[1])
        self.preferences.setComponent(comp[0],interfaces)

    def copyConfig(self):
        d=self.proxy.callRemote('copyConfig')
        d.addCallback(self.preferences.getConfig)
        d.addErrback(self.failedXMLRPC)

    def sendRemoteConfig(self,file,chFile,quit):
        d=self.proxy.callRemote('saveRemoteConfig',file,chFile)
        if quit:
            d.addCallback(self.quiting)
        d.addErrback(self.failedXMLRPC)

    def startConverting(self,gui,dir,filename,videorate,subs,subsFile,subsEnc):
        d=self.proxy.callRemote('startConverting',dir,filename,videorate,subs,subsFile,subsEnc)
        d.addCallback(self.getConvertedId,gui)
        d.addErrback(self.failedXMLRPC)

    def getConvertedId(self,id,gui):
        gui.getConverterId(id)

    def getConverterStatus(self,gui,id):
        d=self.proxy.callRemote('getConverterStatus',id)
        d.addCallback(self.setStatus,gui)
        d.addErrback(self.failedXMLRPC)

    def setStatus(self,status,gui):
        gui.setStatus(status)

    def abortConverter(self,id):
        d=self.proxy.callRemote('abortConverter',id)
        d.addErrback(self.failedXMLRPC)

    def getAvailableStatistics(self,func):
        d=self.proxy.callRemote('getStatistics')
        d.addCallback(self.returnStatistics,func)
        d.addErrback(self.failedXMLRPC)

    def returnStatistics(self,stats,func):
        func(stats)

    def getStatValues(self,func,stats):
        d=self.proxy.callRemote('getStatValues',stats)
        d.addCallback(self.returnStatValues,func)
        d.addErrback(self.failedXMLRPC)

    def returnStatValues(self,stats,func):
        func(stats)

    def startBWMeasurement(self,ip,func):
        func=func.getResults
        d=self.proxy.callRemote('startBWMeasurement',ip)
        d.addCallback(func)
        d.addErrback(self.failedXMLRPC)

    def setBW(self,bw):
        d=self.proxy.callRemote('setBW',bw)
        d.addErrback(self.failedXMLRPC)

    def getBW(self):
        d=self.proxy.callRemote('getBW')
        d.addCallback(self.parent.checkBW)
        d.addErrback(self.failedXMLRPC)

    def restartServer(self):
        d=self.proxy.callRemote('restartServer')
        d.addErrback(self.failedXMLRPC)

    def getNeighbours(self,id,ip,port,func):
        d=self.proxy.callRemote('getNeighbours',id)
        d.addCallback(func,ip,port)

    def getLog(self,func):
        d=self.proxy.callRemote('getLog')
        d.addCallback(func)

    def failedXMLRPC(self,f):
        print 'failed xmlrpc call'
        print f

    def getVizirLogRecords(self,func,ip,port):
        d=self.proxy.callRemote('getRecords')
        d.addCallback(self.loadRecords)
        d.addCallback(func,ip,port)
        d.addErrback(self.failedXMLRPC)

    def stopSwapping(self,stop,id):
        d=self.proxy.callRemote('stopSwapping',stop,id)
        d.addErrback(self.failedXMLRPC)

    def getLogRecords(self,func):
        d=self.proxy.callRemote('getRecords')
        d.addCallback(self.loadRecords)
        d.addCallback(func)
        d.addErrback(self.failedXMLRPC)

    def getStats(self,func,sid,ip,port):
        d=self.proxy.callRemote('getStats',sid)
        d.addCallback(func,ip,port)
        d.addErrback(self.failedStats,func,ip,port)

    def failedStats(self,f,func,ip,port):
        func(-1,ip,port)

    def copyStatFile(self,filename):
        d=self.proxy.callRemote("copyStatFile",filename)
        return d
