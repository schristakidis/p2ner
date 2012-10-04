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


import sys, socket
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from p2ner.abstract.network import Network

class UDPControlMessages(Network, DatagramProtocol):
    
    def initNetwork(self, port = 50000, interface=""):
        self.port = port
        self.interface = interface
        self.log.info('UPDCM component loaded')
        #self.externalPort=port
    
    def listen(self):
        if "listener" in self:
            return
   
        while True:
            try:
                self.listener = reactor.listenUDP(self.port, self) #, interface=self.interface)
                print "PORT: ",self.port
                break
            
            except:
                self.port = self.port+1
        
        self.log.info('start listening to port:%d',self.port)
        
        if 'win' in sys.platform:
            sockhandler = self.listener.getHandle()
            sockhandler.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131071)
            
    def datagramReceived(self, data, (host, port)):
        self.controlPipe.receive(data, (host, port))

    def send(self, data, peer):
        #print "SEND", peer, len(data)
        self.listener.write(data, (peer.ip, peer.port))
        return data
    
    def cleanUp(self):
        if "listener" in self:
            self.listener.stopListening()
            
    def doStop(self):
        self.log.debug('stop listening to port %d',self.port)
        self.listener.stopListening()
        


if __name__ == "__main__":
    u = UDPControlMessages()
    v = UDPControlMessages()
    print u.port, v.port
    u.listen()
    v.listen()
    print u.port, v.port
