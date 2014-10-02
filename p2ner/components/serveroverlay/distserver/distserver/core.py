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
from p2ner.base.Stream import Stream
from messages.requeststream import RequestStreamMessage,AskInitNeighsMessage,AskServerForStatus
from messages.startstopserver import ServerStartedMessage, ServerStoppedMessage, StartRemoteMessage
from messages.messageobjects import PeerListMessage, PeerRemoveMessage, StreamMessage,PeerListProducerMessage,PeerRemoveProducerMessage,SuggestNewPeerMessage,SuggestMessage,ReturnPeerStatus
from messages.startstopclient import ClientStoppedMessage
from p2ner.base.ControlMessage import ControlMessage
from p2ner.core.components import loadComponent
from random import choice,shuffle

class DistServer(Overlay):

    def registerMessages(self):
        self.messagess = []
        self.log.debug('registering messages')
        self.messagess.append(RequestStreamMessage())
        self.messagess.append(ServerStartedMessage())
        self.messagess.append(ServerStoppedMessage())
        self.messagess.append(StartRemoteMessage())
        self.messagess.append(ClientStoppedMessage())
        self.messages.append(SuggestNewPeerMessage())
        self.messages.append(AskInitNeighsMessage())
        self.messages.append(AskServerForStatus())

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
        self.neighbourhoods = {}
        self.peers=[]
        self.superPeers=[]
        self.basePeers=[]
        self.superThres=1000


    def returnPeerStatus(self,peer,bw):
        status=bw>self.superThres
        print peer,' is a Super Peer ',status
        ReturnPeerStatus.send(self.stream.id,status,peer,self.controlPipe)


    def getNeighbours(self, peer=None):
        if not peer:
            return self.neighbourhoods.keys()
        if peer in self.neighbourhoods:
            return self.neighbourhoods[peer]
        return None

    def sendStream(self, peer):
        self.log.debug('sending stream message to %s',peer)
        StreamMessage.send(self.stream, peer, self.controlPipe)


    def addNeighbour(self,peer,superPeer,interOverlay):
        newPeerNeighs = []
        if superPeer:
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

            self.superPeers.append(peer)


        if peer not in self.peers:
            self.log.debug('sending %s as producer to %s',self.producer,peer)
            print 'sending %s as producer to %s'%(self.producer,peer)
            PeerListProducerMessage.send(self.stream.id, [self.producer],peer, self.controlPipe)
            self.peers.append(peer)


    def removeNeighbour(self, peer):
        if peer in self.neighbourhoods:
            for p in self.neighbourhoods[peer]:
                #self.log.debug('sending peerRemove message for %s to %s',peer,p)
                #PeerRemoveMessage.send(self.stream.id, [peer], p, self.controlPipe)
                self.log.debug('removing %s from the neighborhood of %s',peer,p)
                self.neighbourhoods[p].remove(peer)
            #self.log.debug('sending peerRemove message for %s to producer %s',peer,self.producer)
            #PeerRemoveProducerMessage.send(self.stream.id, [peer], self.producer, self.controlPipe)
            #if peer in self.producerNeighbours:
            #    print 'removing peer rom neigbourood'
            #   self.producerNeighbours.remove(peer)
            print 'removing ',peer
            self.log.debug('removing %s',peer)
            del self.neighbourhoods[peer]
            return True
        return False

    def isNeighbour(self, peer):
        return  peer in self.neighbourhoods.keys() or peer==self.producer


    def findNeighbours(self, number):
        list = self.neighbourhoods.keys()
        list.sort(key = lambda a: len(self.neighbourhoods[a]))
        return list[:number]


    def stop(self):
        self.log.info('deleting neighborhood')
        self.neighbourhoods = {}
        self.stream.live=False

    def removes(self):
        self.messagess=[]
        self.stop()

    def getPeers(self):
        return self.neighbourhoods.keys()

    def suggestNewPeer(self,peer,neighs):
        avNeighs=[p for p in self.getNeighbours() if p!=peer and p not in neighs]
        if avNeighs:
            avNeighs=[choice(avNeighs)]
        SuggestMessage.send(self.stream.id,avNeighs,peer,self.controlPipe)
