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


from p2ner.abstract.pipeelement import PipeElement
import sys, socket
from twisted.internet import reactor, defer
from twisted.internet.protocol import DatagramProtocol
import time
from random import uniform

class UDPPortElement(PipeElement, DatagramProtocol):

    def initElement(self, port=50000, interface='', to='port', **kwargs):
        self.port = port
        self.exPort=port
        self.interface = interface
        self.to = to
        self.log.info('UDPPortElement component loaded')

    def getExPort(self,d):
        return self.exPort

    def getPort(self):
        return self.port

    def setPort(self,port):
        self.port=port

    def listen(self, d):
        if "listener" in self:
            return

        self.listener = reactor.listenUDP(self.port, self) #, interface=self.interface)
        self.log.info('start listening to port:%d',self.port)

        print 'listening to port  ',self.port

        if sys.platform == 'win32':
            sockhandler = self.listener.getHandle()
            sockhandler.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131071)
            sockhandler.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131071)

    def datagramReceived(self, data, (host, port)):
        recTime = time.time()
        d = self.forwardprev("receive", (host, port), recTime)
        #reactor.callLater(0, d.callback, data)
        d.callback(data)

    def send(self, res, msg, data, peer):
        to=self.to

        useLocalIp=False
        try: #for the server
            if self.root.netChecker.nat and peer.ip==self.root.netChecker.externalIp:
                useLocalIp=True
                peer.useLocalIp=True
        except:
            pass

        if peer.useLocalIp:
            ip=peer.lip
            to='l'+to
        else:
            ip=peer.ip



        #print 'send to:',ip,to,getattr(peer, to)

        if isinstance(res, (list, tuple)):
            for r in res:
               self.sockwrite(r, ip, getattr(peer, to))
        else:
            self.sockwrite(res, ip, getattr(peer, to))
        return res

    def sockwrite(self, data, host, port):
        if len(data):
            self.listener.write(data, (host, port))
        return data

    def cleanUp(self, d=None):
        if "listener" in self:
            self.listener.stopListening()

    def doStop(self, d=None):
        self.log.debug('stop listening to port %d',self.port)
        print self.port
        self.listener.stopListening()



