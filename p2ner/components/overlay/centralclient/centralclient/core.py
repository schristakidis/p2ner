# -*- coding: utf-8 -*-

from p2ner.abstract.overlay import Overlay
from messages.peerlistmessage import PeerListMessage, RequestNeighbours,PeerListPMessage
from messages.peerremovemessage import PeerRemoveMessage

class CentralClient(Overlay):
    
    def registerMessages(self):
        self.messages = []
        self.messages.append(PeerListMessage())
        self.messages.append(PeerRemoveMessage())
        self.messages.append(PeerListPMessage())
        
    def initOverlay(self):
        self.log.info('initing overlay')
        print 'initing overlay'
        self.sanityCheck(["stream", "control", "controlPipe"])
        self.registerMessages()
        self.neighbours = []

        
    def getNeighbours(self):
        return self.neighbours[:]
    
    def addNeighbour(self, peer):
        if not self.isNeighbour(peer):
            if self.netChecker.nat and peer.ip==self.netChecker.externalIp:
                peer.useLocalIp=True
            self.neighbours.append(peer)
            self.log.info('adding %s to neighborhood',peer)
        else:
            self.log.error("%s  yet in overlay" ,peer)
            raise ValueError("%s peer yet in overlay" % str(peer))
        print '--------------------'
        for p in self.neighbours:
            print p,p.useLocalIp,p.lip
            print p.reportedBW
            
    def removeNeighbour(self, peer):
        try:
            self.neighbours.remove(peer)
            self.log.info('removing %s from neighborhood',peer)
        except:
            self.log.error('%s is not a neighbor',peer)
                    
    def isNeighbour(self, peer):
        return peer in self.neighbours
    
    def stop(self):
        self.log.info('stopping overlay')
        


if __name__ == "__main__":
    a = CentralClient()
