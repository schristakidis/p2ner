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


from twisted.internet import reactor
from p2ner.abstract.overlay import Overlay
from messages.requeststream import RequestStreamMessage,AskInitNeighsMessage,AskServerForStatus
from messages.startstopserver import ServerStartedMessage, ServerStoppedMessage, StartRemoteMessage
from messages.messageobjects import PeerListMessage, StreamMessage,PeerListProducerMessage,SuggestNewPeerMessage,SuggestMessage,ReturnPeerStatus
from messages.startstopclient import ClientStoppedMessage,ClientDied
from p2ner.core.components import loadComponent
from random import choice,shuffle

class DistServer(Overlay):

    def registerMessages(self):
        self.messages = []
        self.log.debug('registering messages')
        self.messages.append(RequestStreamMessage())
        self.messages.append(ServerStartedMessage())
        self.messages.append(ServerStoppedMessage())
        self.messages.append(StartRemoteMessage())
        self.messages.append(ClientStoppedMessage())
        self.messages.append(SuggestNewPeerMessage())
        self.messages.append(AskInitNeighsMessage())
        self.messages.append(AskServerForStatus())
        self.messages.append(ClientDied())

    def initOverlay(self, producer, stream):
        self.log=self.logger.getLoggerChild(('s'+str(stream.id)),self.interface)
        self.log.info('initing overlay')
        self.overlay = self
        self.registerMessages()
        self.baseNeighPeers = stream.overlay['baseNumNeigh']/2
        self.superNeighPeers = stream.overlay['superNumNeigh']/2
        self.interNeighPeers = stream.overlay['interNumNeigh']
        self.producer = producer
        self.stream = stream
        self.superPeers=[]
        self.basePeers=[]
        self.baseInterPeers=[]
        self.superThres=1000


    def returnPeerStatus(self,peer,bw):
        status=bw>self.superThres
        # status=choice([True,False])
        print peer,' is a Super Peer ',status
        ReturnPeerStatus.send(self.stream.id,status,peer,self.controlPipe)

    def sendStream(self, peer):
        self.log.debug('sending stream message to %s',peer)
        StreamMessage.send(self.stream, peer, self.controlPipe)


    def addNeighbour(self,peer,superPeer,interOverlay):
        newPeerNeighs = []
        addProducer=False
        if superPeer:
            if not interOverlay:
                if peer in self.superPeers:
                    raise ValueError('super peer already in list')
                if len(self.superPeers)>0:
                    if len(self.superPeers)<self.superNeighPeers:
                        newPeerNeighs=self.superPeers[:]
                    else:
                        shuffle(self.superPeers)
                        newPeerNeighs=self.superPeers[:self.superNeighPeers]

                    self.log.debug('sending peerlist message to %s containg %s',peer,str(newPeerNeighs))
                    print 'sending peerlist message to %s containg %s'%(peer,str(newPeerNeighs))
                    PeerListMessage.send(self.stream.id, superPeer,interOverlay, newPeerNeighs, peer, self.controlPipe)
            else:
                raise ValueError("super peer should never ask for neighbors in the inter overlay")

            if peer not in self.superPeers:
                addProducer=True

            self.superPeers.append(peer)
        else:
            if not interOverlay:
                if peer in self.basePeers:
                    raise ValueError('base peer already in list')
                if len(self.basePeers)>0:
                    if len(self.basePeers)<self.baseNeighPeers:
                        newPeerNeighs=self.basePeers[:]
                    else:
                        shuffle(self.basePeers)
                        newPeerNeighs=self.basePeers[:self.baseNeighPeers]

                    self.log.debug('sending peerlist message to %s containg %s',peer,str(newPeerNeighs))
                    print 'sending peerlist message to %s containg %s'%(peer,str(newPeerNeighs))
                    PeerListMessage.send(self.stream.id, superPeer,interOverlay, newPeerNeighs, peer, self.controlPipe)

                self.basePeers.append(peer)
                if peer not in self.baseInterPeers:
                    addProducer=True
            else:
                if len(self.superPeers)<self.interNeighPeers:
                    newPeerNeighs=self.superPeers[:]
                else:
                    shuffle(self.superPeers)
                    newPeerNeighs=self.superPeers[:self.interNeighPeers]

                self.log.debug('sending peerlist message to %s containg %s',peer,str(newPeerNeighs))
                print 'sending peerlist message to %s containg %s'%(peer,str(newPeerNeighs))
                PeerListMessage.send(self.stream.id, superPeer,interOverlay, newPeerNeighs, peer, self.controlPipe)

                if peer not in self.baseInterPeers:
                    self.baseInterPeers.append(peer)
                if peer not in self.basePeers:
                    addProducer=True


        if addProducer:
                self.log.debug('sending %s as producer to %s',self.producer,peer)
                print 'sending %s as producer to %s'%(self.producer,peer)
                PeerListProducerMessage.send(self.stream.id, [self.producer],peer, self.controlPipe)






    def removeNeighbour(self, peer):
        if peer not in self.superPeers and peer not in self.basePeers:
            self.log.error("cannot remove peer that it's not in my lists")
            print "cannot remove peer that it's not in my lists"
            return False

        if peer in self.superPeers:
            self.superPeers.remove(peer)
        elif peer in self.basePeers:
            self.basePeers.remove(peer)
            self.baseInterPeers.remove(peer)
        return True

    def isNeighbour(self, peer):
        return  peer in self.superPeers or peer in self.basePeers or peer==self.producer



    def stop(self):
        self.log.info('deleting neighborhood')
        self.superPeers=[]
        self.basePeers=[]
        self.stream.live=False

    def removes(self):
        self.messages=[]
        self.stop()

    def getPeers(self):
        return self.superPeers+self.basePeers

    def getNeighbours(self):
        return self.getPeers()

    def suggestNewPeer(self, peer, superPeer, interOverlay, neighs):
        if superPeer or interOverlay:
            overNeighs=self.superPeers
        else:
            overNeighs=self.basePeers

        avNeighs=[p for p in overNeighs if p!=peer and p not in neighs]
        if avNeighs:
            avNeighs=[choice(avNeighs)]

        if interOverlay:
            superPeer=not superPeer
        SuggestMessage.send(self.stream.id,superPeer,interOverlay,avNeighs,peer,self.controlPipe)
