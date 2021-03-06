# -*- coding: utf-8 -*-
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

from p2ner.abstract.engine import Engine
from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred
from p2ner.core.components import loadComponent
#from p2ner.base.messages.bootstrap import ClientStartedMessage
from messages.streammessage import  StreamIdMessage, ContentsMessage, SubscribeMessage
from messages.messageobjects import RequestStreamMessage,StreamMessage,CheckContentsMessage,ClientStartedMessage
from p2ner.base.Peer import Peer
from cPickle import dumps


defaultStream = ("StreamClient", [], {})

class Client(Engine):

    def initEngine(self, *args, **kwargs):
        self.log.info('initing client')
        self.enableTraffic(cPipe=kwargs['cPipe'])
        self.enableUI(**kwargs)
        self.messages = []
        self.sidListeners = []
        self.checkServers={}
        self.streamListeners=[]
        self.waitingReply=[]
        self.converters={}

        if 'basic' in kwargs and kwargs['basic']:
            self.basic=True
        else:
            self.basic=False
            self.holePuncher=loadComponent('plugin','HolePuncher')(_parent=self)
            self.useHolePunching=True
            self.rProducerInf=loadComponent('plugin','RemoteProducerController')(_parent=self)
        self.chatClient=loadComponent('plugin','ChatClient')(_parent=self)

        sip=None
        sport=None
        if 'vizir' in kwargs['interface'][2].keys() and kwargs['interface'][2]['vizir']:
            sip=kwargs['interface'][2]['vizirIP']
            sport=kwargs['interface'][2]['vizirPort']
        self.netChecker=loadComponent('plugin','NetworkChecker')(sip,sport,_parent=self,)
        reactor.callLater(0.2,self.interface.checkNetwork)


    def checkNatPeer(self):
        if self.basic:
            self.controlPort=self.root.controlPipe.callSimple('getPort')
            self.dataPort=self.root.trafficPipe.callSimple('getPort')
            print self.dataPort
            return None,self.dataPort

        if self.netChecker.upnp:
            port=self.netChecker.upnpDataPort
        else:
            port=self.netChecker.extDataPort

        p=None
        if self.netChecker.nat:
            p=Peer(self.netChecker.localIp,self.netChecker.controlPort,self.netChecker.dataPort)
            if self.netChecker.hpunching:
                p.hpunch=True
            p.natType=self.netChecker.natType
        return p,port

    def getPeerObject(self):
        if self.netChecker.upnp:
            cPort=self.netChecker.upnpControlPort
            dPort=self.netChecker.upnpDataPort
        else:
            cPort=self.netChecker.extControlPort
            dPort=self.netChecker.extDataPort

        extIP=self.netChecker.externalIp
        lIP=self.netChecker.localIp

        p=Peer(extIP,cPort,dPort)

        if extIP==lIP or self.basic:
            return p

        p.lip=lIP
        p.lport=self.netChecker.controlPort
        p.ldataPort=self.netChecker.dataPort
        p.natType=self.netChecker.natType
        p.hpunch=self.netChecker.hpunching
        return p

    def registerStream(self,stream,input,output):
        print output['comp']
        p=stream.getServer()
        server=Peer(p[0],p[1])
        #server.dataPort=int(p[1])+1

        p,port=self.checkNatPeer()

        bw=int(self.trafficPipe.callSimple('getBW')/1024)
        reactor.callLater(0.1, ClientStartedMessage.send, port,bw, p,server, self.controlPipe)
        self.log.debug('adding stream id message to listeners')
        m=StreamIdMessage(stream,input,output)
        self.sidListeners.append(m)
        self.log.debug('sending stream message to %s',server)
        reactor.callLater(0.5,StreamMessage.send,stream, server, self.controlPipe,m.checkResponse)


    def newStream(self, stream,input,output):
        if self.getPStream(stream.id):
            self.log.error('stream with id %d already exists',stream.id)
            raise ValueError("Stream already exists")
        s, a, k = ('StreamProducer',[],{})

        self.log.debug('trying to load %s',s)
        streamComponent = loadComponent("stream", s)
        k['stream']=stream
        if input:
            k['input']=(input['component'],[],{'input':input})
        if output:
            k['output']=(output['comp'],[],{'output':output['kwargs']})

        self.producingStreams.append(streamComponent( _parent=self,**k))


    def contactServers(self,server):
        server=Peer(server[0],server[1])
        if server in self.checkServers.keys():
            return


        """
        if self.netChecker.upnp:
            port=self.netChecker.upnpDataPort
        else:
            port=self.netChecker.extDataPort

        reactor.callLater(0.1, ClientStartedMessage.send, port, None,server, self.controlPipe)
        """


        m=ContentsMessage(server)
        self.checkServers[server]=m

        self.log.debug('sending check contents message to %s',server)
        reactor.callLater(0.5, CheckContentsMessage.send,server,self.controlPipe,m.checkResponse)


    def startProducing(self,id):
        stream=self.getPStream(id)
        if stream:
            stream.start()
            self.log.info('started producing')

        #self.interface.returnStartProducing('produce')




    def subscribeStream(self,id,ip,port,output=None):
        if id in self.waitingReply:
            return

        if self.getStream(id):
            self.log.error('stream with id %d already exists',id)
            #raise ValueError("Stream already exists")
            return

        self.waitingReply.append(id)
        server=Peer(ip,port)
        #server.dataPort=int(port)+1
        self.log.debug('sending client started message to %s',server)

        p,port=self.checkNatPeer()

        bw=int(self.trafficPipe.callSimple('getBW')/1024)
        reactor.callLater(0.1, ClientStartedMessage.send, port,bw,p,server, self.controlPipe)
        self.log.debug('sending request stream message to %s',server)
        m=SubscribeMessage(id,output)
        self.streamListeners.append(m)
        reactor.callLater(0.5, RequestStreamMessage.send, id, server, self.controlPipe,m.checkResponse)


    def newSubStream(self,stream,id,output):
        self.waitingReply.remove(id)
        if stream!=-1:
            s, a, k = ('StreamClient',[],{})
            self.log.debug('trying to load %s',s)
            streamComponent = loadComponent("stream", s)
            k['stream']=stream
            if output:
                k['output']=(output['comp'],[],{'output':output['kwargs']})

            self.streams.append(streamComponent( _parent=self,**k))
        self.interface.returnSubStream(stream,id)

    def start(self):
        pass

    def startRemoteProducer(self,id):
        stream=self.getStream(id)
        if not stream:
            return
        stream.startRemoteProducer()
        return True


    def stopProducing(self,id,changeRepub=False):
        stream=self.getPStream(id)
        if not stream:
            self.log.error("stream with id:%d doesn't exist",id)
            #raise ValueError('there is not such stream %d',id)
            return

        if changeRepub:
            stream.stream.republish=False

        stream.stop()

        self.interface.returnStopProducing(id)


    def unregisterStream(self,id):
        stream=self.getStream(id)
        if not stream:
            self.log.error("stream with id:%d doesn't exist",id)
            #raise ValueError('there is not such stream %d',id)
            return

        stream.stop()

        self.interface.returnUnregisterStream(id)

    def exiting(self):
        for s in self.getAllStreams():
            s.stop()
        self.interface.stop()
        reactor.callLater(1,self.quit)

    def quiting(self):
        self.exiting()
        #reactor.stop()

    def startConverting(self,dir,filename,videorate,subs,subsFile,subsEnc):
        id=len(self.converters.keys())
        self.converters[id]=loadComponent('plugin','Converter')()
        self.converters[id].startConverting(dir,filename,videorate,subs,subsFile,subsEnc)
        return id

    def startBWMeasurement(self,ip,gui=None,defer=None):
        loadComponent('plugin','TCPBandwidthClient')(ip,gui,defer).start()

    def setBW(self,bw):
        self.trafficPipe.call('setBW',bw)

def startClient():
    from twisted.internet import reactor
    import sys,getopt
    try:
        optlist,args=getopt.getopt(sys.argv[1:],'bp:dv:P:hsc',['basic','port=','daemon','vizir=','vizirPort=','help','stats','cPipe'])
    except getopt.GetoptError as err:
        usage(err=err)

    basic=False
    interface='LocalControl'
    port=50000
    vizir=False
    vPort=9000
    stat=None
    cPipe=True
    for opt,a in optlist:
        if opt in ('-b','--basic'):
            basic=True
        elif opt in ('-p','--port'):
            port=int(a)
        elif opt in ('-d','--daemon'):
            interface='XMLRPCControlUI'
        elif opt in ('-v','--vizir'):
            vizir=True
            interface='XMLRPCControlUI'
            vIP=a
        elif opt in ('-P','--vizirPort'):
            vPort=int(a)
        elif opt in ('-s','--stats'):
            stat='ZabbixStats'
        elif opt in ('-c','--cPipe'):
            cPipe=False
        elif opt in ('-h','--help'):
            usage()
    if interface=='XMLRPCControlUI':
        gui=None
        if vizir:
            kwargs={'vizir':vizir,'vizirIP':vIP,'vizirPort':vPort}
        else:
            kwargs={}
    else:
        gui=('GtkGui',[],{})
        kwargs={}

    if not stat:
        P2NER = Client(_parent=None,interface=(interface,[],kwargs),UI=gui,basic=basic,port=port,cPipe=cPipe)
    else:
        P2NER = Client(_parent=None,interface=(interface,[],kwargs),UI=gui,basic=basic,port=port,stats=stat,cPipe=cPipe)
    reactor.run()

def startBasicNetClient():
    from twisted.internet import reactor
    P2NER = Client(_parent=None,UI=('GtkGui',[],{}),basic=True)

    reactor.run()

def startDaemonClient():
    from twisted.internet import reactor
    import sys,getopt
    try:
        optlist,args=getopt.getopt(sys.argv[1:],'bp:v:P:chs',['basic','port=','vizir=','vizirPort=','help','stats'])
    except getopt.GetoptError as err:
        usage(err=err,daemon=True)

    basic=False
    port=50000
    vizir=False
    vPort=9000
    stat=None
    cPipe=True
    for opt,a in optlist:
        if opt in ('-b','--basic'):
            basic=True
        elif opt in ('-p','--port'):
            port=int(a)
        elif opt in ('-v','--vizir'):
            vizir=True
            vIP=a
        elif opt in ('-P','--vizirPort'):
            vPort=int(a)
        elif opt in ('-s','--stats'):
            stat='ZabbixStats'
        elif opt in ('-c','--cPipe'):
            cPipe=False
        elif opt in ('-h','--help'):
            usage(daemon=True)

    if vizir:
        kwargs={'vizir':True,'vizirIP':vIP,'vizirPort':vPort}
    else:
        kwargs={}
    if not stat:
        P2NER = Client(_parent=None,interface=('XMLRPCControlUI',[],kwargs),basic=basic,port=port,cPipe=cPipe)
    else:
        P2NER = Client(_parent=None,interface=('XMLRPCControlUI',[],kwargs),stats=stat,basic=basic,port=port,cPipe=cPipe)
    reactor.run()

def usage(err=None,daemon=False):
    import sys
    if err:
        print str(err)
    print ' -------------------------------------------------------------------------'
    if not daemon:
        print ' Run P2ner Client'
    else:
        print ' Run P2ner Daemon'
    print ' '
    print ' -b, --basic  :run with basic network configuration'
    print ' -p, --port port :define port'
    if not daemon:
        print ' -d, --daemon :run p2ner daemon with XMLRPC interface'
    print ' -v, --vizir [ip] :run daemon with XMLRPC and vizir interface and connect to ip'
    print ' -P, --vizirPort port :set the vizir controller port'
    print '-s, --stats : enable Zabbix Statistics'
    print '-c, --cPipe : disable c traffic Pipeline'
    print ' -h, --help :print help'
    print ' -------------------------------------------------------------------------'
    sys.exit(' ')

if __name__ == "__main__":
    startClient()
