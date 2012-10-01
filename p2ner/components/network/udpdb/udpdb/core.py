# -*- coding: utf-8 -*-

import sys, socket
from twisted.internet import reactor
from twisted.internet.udp import EWOULDBLOCK
from twisted.internet.protocol import DatagramProtocol
from p2ner.abstract.network import Network

class UDPDataBlocks(Network, DatagramProtocol):
    
    def initNetwork(self, port = 50001, interface=""):
        self.port = port
        self.interface = interface
        #self.externalPort=port
    
    def listen(self):
        if "listener" in self:
            return
        while True:
            try:
                self.listener = reactor.listenUDP(self.port, self, interface=self.interface)
                break
            
            except:
                self.port = self.port+1
                
        self.log.info('start listening to port:%d',self.port)
       
        
        if 'win' in sys.platform:
            sockhandler = self.listener.getHandle()
            sockhandler.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131071)

    def datagramReceived(self, data, (host, port)):
        #print "DATA RECEIVED", len(data), host, port
        self.trafficPipe.receive(data, (host, port))

    def send(self, data, peer):
        host, port = peer.ip, peer.dataPort
        try:
            #print "SEND BLOCK:", len(data), "BYTES", peer 
            self.listener.write(data, (host, port))
        except socket.error, no:
            if no[0] == EWOULDBLOCK:
                reactor.callLater(0, self.listener.write, data, (host, port))
        return data
    
    def cleanUp(self):
        if "listener" in self:
            self.listener.stopListening()

    def doStop(self):
        self.log.debug('stop listening to port %d',self.port)
        self.listener.stopListening()
