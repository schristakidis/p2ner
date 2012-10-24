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


from p2ner.abstract.overlay import Overlay
from messages.peerlistmessage import PeerListMessage,PeerListPMessage,AddNeighbourMessage
from messages.peerremovemessage import ClientStoppedMessage

class CentralClient(Overlay):
    
    def registerMessages(self):
        self.messages = []
        self.messages.append(PeerListMessage())
        self.messages.append(ClientStoppedMessage())
        self.messages.append(PeerListPMessage())
        self.messages.append(AddNeighbourMessage())
        
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
            #if self.netChecker.nat and peer.ip==self.netChecker.externalIp:
             #   peer.useLocalIp=True
            self.neighbours.append(peer)
            self.log.info('adding %s to neighborhood',peer)
        else:
            self.log.error("%s  yet in overlay" ,peer)
            raise ValueError("%s peer yet in overlay" % str(peer))
        print '--------------------'
        print 'NEW NEIGH'
        for p in self.neighbours:
            print p,p.useLocalIp,p.lip
            print p.reportedBW
            
    def failedNeighbour(self,peer):
        self.log.warning('failed to add %s to neighborhood',peer)
        print 'failed to add ',peer,' to neighbourhood'
      
    def addProducer(self,peer):
        self.producer=peer
        self.log.info('adding %s as producer',peer)
        print 'adding ',peer,' as producer'
        
    def failedProducer(self,peer):
        self.log.warning('failed to add %s as producer',peer)
        print 'failed to add ',peer,' as producer'
          
    def removeNeighbour(self, peer):
        try:
            self.neighbours.remove(peer)
            self.log.info('removing %s from neighborhood',peer)
            print 'removing form neighbourhood ',peer
        except:
            self.log.error('%s is not a neighbor',peer)
                    
    def isNeighbour(self, peer):
        return peer in self.neighbours
    
    def stop(self):
        self.log.info('stopping overlay')
        self.log.debug('sending clientStopped message to %s',self.server)
        ClientStoppedMessage.send(self.stream.id, self.server, self.controlPipe)
        ClientStoppedMessage.send(self.stream.id, self.producer, self.controlPipe)
        for n in self.getNeighbours():
            self.log.debug('sending clientStopped message to %s',n)
            ClientStoppedMessage.send(self.stream.id, n, self.controlPipe)
        


if __name__ == "__main__":
    a = CentralClient()
