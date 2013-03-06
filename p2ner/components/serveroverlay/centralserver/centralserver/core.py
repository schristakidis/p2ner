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
from messages.requeststream import RequestStreamMessage
from messages.startstopserver import ServerStartedMessage, ServerStoppedMessage, StartRemoteMessage
from messages.messageobjects import PeerListMessage, PeerRemoveMessage, StreamMessage,PeerListProducerMessage,PeerRemoveProducerMessage,SuggestNewPeerMessage,SuggestMessage
from messages.startstopclient import ClientStoppedMessage
from p2ner.base.ControlMessage import ControlMessage
from p2ner.core.components import loadComponent
from random import choice

class CentralServer(Overlay):
    
    def registerMessages(self):
        self.messagess = []
        self.log.debug('registering messages')
        self.messagess.append(RequestStreamMessage())
        self.messagess.append(ServerStartedMessage())
        self.messagess.append(ServerStoppedMessage())
        self.messagess.append(StartRemoteMessage())
        self.messagess.append(ClientStoppedMessage())
        self.messages.append(SuggestNewPeerMessage())
    
    def initOverlay(self, producer, stream):
        self.log=self.logger.getLoggerChild(('s'+str(stream.id)),self.interface)
        self.log.info('initing overlay')
        self.overlay = self
        self.sanityCheck(["controlPipe", "overlay"])
        self.registerMessages()
        self.maxPeers = stream.overlay['numNeigh']/2
        self.producer = producer
        self.stream = stream
        #self.producerNeighbours = []
        self.neighbourhoods = {}
        
        if self.drawPlots:
            self.vizInterface = loadComponent('plugin', 'VizNetInterface')(_parent=self)
            self.vizPlot= loadComponent('plugin', 'OverlayViz')() 
            self.vizPlot.start(self.vizInterface)
        
    def getNeighbours(self, peer=None):
        if not peer:
            #print "KEYYAZ:", self.neighbourhoods.keys()
            return self.neighbourhoods.keys()
        if peer in self.neighbourhoods:
            # print "PEEYAZ:", self.neighbourhoods[peer]
            return self.neighbourhoods[peer]
        print "UAZ"
        return None
    
    def addNeighbour(self, peer):
        self.log.debug('sending stream message to %s',peer)
        StreamMessage.send(self.stream, peer, self.controlPipe,self._addNeighbour)
        
    def _addNeighbour(self,peer):
        newPeerNeighs = []
        if len(self.neighbourhoods) > 0:
            if len(self.neighbourhoods) < self.maxPeers:
                newPeerNeighs = self.neighbourhoods.keys()
            else:
                newPeerNeighs = self.findNeighbours(self.maxPeers)
            for p in newPeerNeighs:
                self.log.debug('adding %s to the neighborhood of %s',peer,p)
                self.neighbourhoods[p].append(peer)
                self.log.debug('sending peerlist message to %s containing %s',p,peer)
                #PeerListMessage.send(self.stream.id, [peer], p, self.controlPipe)
            self.neighbourhoods[peer] = newPeerNeighs
            self.log.debug('sending peerlist message to %s containg %s',peer,str(newPeerNeighs))
            PeerListMessage.send(self.stream.id, newPeerNeighs, peer, self.controlPipe)
        self.neighbourhoods[peer] = newPeerNeighs
        n=''.join(str(newPeerNeighs))
        self.log.debug('the neighbors of %s are %s',peer,n)
        #self.capConnections()
        #self.updateProducerNeighbourhood()
        self.log.debug('sending peerList message to producer %s:%s',self.producer,peer)
        #PeerListProducerMessage.send(self.stream.id, [peer], self.producer, self.controlPipe)
        PeerListProducerMessage.send(self.stream.id, [self.producer],peer, self.controlPipe)
    
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
    
    def capConnections(self):
        overConnected = [p for p in self.neighbourhoods if len(self.neighbourhoods[p])>self.maxPeers]
        for p in overConnected:
            delta = len(self.neighbourhoods[p])-self.maxPeers
            overNeighs = [n for n in self.neighbourhoods[p] if len(self.neighbourhoods[n])>self.maxPeers]
            for i in range(min(delta, len(overNeighs))):
                self.log.debug('sending peerRemove message for %s to  %s',p,overNeighs[i])
                PeerRemoveMessage.send( self.stream.id, [p], overNeighs[i], self.controlPipe)
                self.neighbourhoods[overNeighs[i]].remove(p)
                self.log.debug('sending peerRemove message for %s to  %s',overNeighs[i],p)
                PeerRemoveMessage( self.stream.id, [overNeighs[i]], p,self.controlPipe)
                self.neighbourhoods[p].remove(overNeighs[i])


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
