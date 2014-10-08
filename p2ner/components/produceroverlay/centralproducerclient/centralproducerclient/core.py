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
from messages.peerlistmessage import AddProducerMessage
from messages.peerremovemessage import ClientStoppedMessage,ClientDied
from twisted.internet import reactor

class CentralClient(Overlay):

    def registerMessages(self):
        self.messages = []
        self.messages.append(AddProducerMessage())
        self.messages.append(ClientStoppedMessage())
        self.messages.append(ClientDied())

    def initOverlay(self):
        self.log.info('initing producer overlay')
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
            if  self.scheduler.loopingCall.running:
                reactor.callLater(0.1, self.scheduler.sendLPB, peer)
        else:
            self.log.error("%s  yet in overlay" ,peer)
            raise ValueError("%s peer yet in overlay" % str(peer))

    def removeNeighbour(self, peer):
        try:
            self.neighbours.remove(peer)
            self.log.info('removing %s from neighborhood',peer)
            print 'removing from producer neighborhood ',peer
        except:
            self.log.error('%s is not a neighbor',peer)

    def isNeighbour(self, peer):
        return peer in self.neighbours

    def stop(self):
        self.log.info('stopping overlay')



if __name__ == "__main__":
    a = CentralClient()
