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
from p2ner.core.components import loadComponent,getComponents
from messages.publishstream import PublishStreamMessage
from messages.startstopclient import ClientStartedMessage
from messages.checkcontents import CheckContentsMessage
from messages.messageobjects import StreamIdMessage,ContentsMessage
from messages.pingmessage import KeepAliveMessage,AskServerPunchMessage
from hashlib import md5
from time import localtime

defaultStream = ("StreamClient", [], {})


class Server(Engine):

    def registerMessages(self):
        self.log.debug('registering messages')
        self.messages = []
        self.messages.append(PublishStreamMessage())
        self.messages.append(ClientStartedMessage())
        self.messages.append(CheckContentsMessage())
        self.messages.append(KeepAliveMessage())
        self.messages.append(AskServerPunchMessage())

    def initEngine(self, *args, **kwargs):
        self.sanityCheck(["control", "controlPipe"])
        self.enableTraffic(cPipe=True)
        self.registerMessages()
        self.overlays = {}
        self.knownPeers = []
        self.log.info('server initiated')
        self.bandwidthServer=loadComponent('plugin','TCPBWServer')()
        self.bandwidthServer.startListening()
        self.controlPipe.call('listen')
        self.trafficPipe.call('listen')
        self.chatServer=loadComponent('plugin','ChatServer')(_parent=self)
        self.drawPlots=False
        if 'plot' in kwargs:
            self.drawPlots=kwargs['plot']
        #self.startweb()

    def startweb(self):
        ws = ("ServerWebUI", [], {"serverport":8880})
        s, a, k = ws
        webserver = loadComponent("ui", s)
        self.webserver = webserver(_parent=self, *a, **k)

    def start(self, sid):
        pass


    def hasStream(self, streamId):
        #return streamId in [ov.stream.id for ov in self.overlays]
        return streamId in self.overlays.keys()

    def generateStreamId(self,p,s):
        m=md5()
        m.update(p.getIP()+str(p.getPort())+s[0]+str(s[1])+str(localtime()))
        h=m.hexdigest()
        h=h[:len(h)/8]
        id=int(h,16)
        while True:
            if not self.hasStream(id):
                break
            id += 1
        self.log.info('new stream id is %d',id)
        return id

    def newStream(self, producer, stream):
        overlay = ("DistServer", [producer, stream], {})
        s, a, k = overlay
        self.log.debug('trying to load overlay %s',s)
        ov = loadComponent("serveroverlay", s)
        #self.overlays.append(ov(_parent=self, *a, **k))
        self.overlays[stream.id]=ov(_parent=self, *a, **k)
        self.log.info('new stream %s',stream)
        StreamIdMessage.send(stream.id, stream.streamHash(), producer, self.controlPipe)
        self.chatServer.newRoom(stream.id)

    def sendContents(self,peer):
        #s=[ov.stream for ov in self.overlays]
        s=[ov.stream for ov in self.overlays.values()]
        ContentsMessage.send(s,peer,self.controlPipe)

    def unregisterStream(self,id):
        try:
            ov=self.overlays.pop(id)
            ov.removes()
            self.log.info('unregistering stream:%s',ov.stream)
            self.chatServer.removeRoom(id)
        except:
            self.log.error("could not unregister stream:%d because it doesn't exist",id)
            #raise ValueError("could not unregister stream because it doesn't exist")

    def restartServer(self):
        for ov in self.overlays.values():
            ov.removes()
            self.log.info('unregistering stream:%s',ov.stream)
            self.chatServer.removeRoom(id)
        self.overlays={}
        print 'server restarted'

def startServer():
    from twisted.internet import reactor
    import sys,getopt
    try:
        optlist,args=getopt.getopt(sys.argv[1:],'p:v:P:hg',['port=','vizir=','vizirPort=','help','graph'])
    except getopt.GetoptError as err:
        usage(err=err)


    interface='NullControl'
    port=16000
    vizir=False
    vPort=9000
    plots=False
    for opt,a in optlist:
        if opt in ('-p','--port'):
            port=int(a)
        elif opt in ('-v','--vizir'):
            vizir=True
            interface='ServerXMLRPCControl'
            vIP=a
        elif opt in ('-P','--vizirPort'):
            vPort=int(a)
        elif opt in ('-g','--graph'):
            plots=True
        elif opt in ('-h','--help'):
            usage()

    if interface=='ServerXMLRPCControl':
        kwargs={'vizir':vizir,'vizirIP':vIP,'vizirPort':vPort}
    else:
        kwargs={}

    mkwargs={'plot':plots}

    P2NER = Server(_parent=None, control = ("UDPCM", [], {"port":port}),logger=('Logger',{'name':'p2nerServer','server':True}),interface=(interface,[],kwargs),**mkwargs)
    reactor.run()

def usage(err=None):
    import sys
    if err:
        print str(err)
    print ' -------------------------------------------------------------------------'
    print ' Run P2ner Server'
    print ' '
    print ' -p, --port port :define port'
    print ' -v, --vizir [ip] :run server with XMLRPC and vizir interface and connect to ip'
    print ' -P, --vizirPort port :set the vizir controller port'
    print ' -g, --graph :enable overlay visualization'
    print ' -h, --help :print help'
    print ' -------------------------------------------------------------------------'
    sys.exit(' ')

if __name__ == "__main__":
    startServer()
