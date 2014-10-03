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


import sys
from p2ner.abstract.overlay import Overlay
from messages.producermessage import *
from messages.bootstrapmessages import *
from messages.peerremovemessage import InformClientStoppedMessage
from messages.vizirmessages import *
from twisted.internet import task,reactor,defer
from random import choice,uniform
from bwmeasurement import FlowBwMeasurement
from subclient import SubOverlay


class OverlayManager(Overlay):

    def registerMessages(self):
        self.messages = []
        self.messages.append(PeerListPMessage())
        self.messages.append(GetPeerStatusMessage())
        self.messages.append(GetNeighsMessage())

    def initOverlay(self):
        self.log=self.logger.getLoggerChild(('o'+str(self.stream.id)),self.interface)
        self.log.info('initing overlay')
        print 'initing overlay'
        self.sanityCheck(["stream", "control", "controlPipe"])

        self.registerMessages()

        self.subOverlays={}
        self.stopDefer=None
        self.waitingToStop={}
        self.neighbours = []
        self.baseNumNeigh=self.stream.overlay['baseNumNeigh']
        self.superNumNeigh=self.stream.overlay['superNumNeigh']
        self.interNumNeigh=self.stream.overlay['interNumNeigh']
        self.swapFreq=self.stream.overlay['swapFreq']

        self.capacity=self.trafficPipe.callSimple('getReportedCap')
        if self.capacity:
            self.resolveStatus()
        else:
            d=FlowBwMeasurement(self.stream.server,_parent=self).start()
            d.addCallback(self.resolveStatus)

    def resolveStatus(self,cap=None):
        if cap:
            self.capacity=cap
        AskServerForStatus.send(self.stream.id,self.capacity,self.server, self.resolveStatusFailure,self.controlPipe)

    def resolveStatusFailure(self,err):
        self.log.error('failed to get status from server')
        self.stream.stop()

    def formSubOverlays(self,superPeer):
        self.superPeer=superPeer
        if superPeer:
            print "I am a super PEERRRRRRRRRRRRRRRRRRRRRRRRRRR"
            self.subOverlays['super']=SubOverlay(self.superNumNeigh,self.swapFreq,superOverlay=True,interOverlay=False,_parent=self)
            self.subOverlays['base']=SubOverlay(self.superNumNeigh,self.swapFreq,superOverlay=False,interOverlay=False,_parent=self)
        else:
            print "just a normal peer"


    def getNeighbours(self):
        neighs=[]
        for ov in self.subOverlays.values():
            neighs +=ov.getNeighbours()
        return neighs


    def isNeighbour(self, peer):
        return peer in self.getNeighbours()


    def addProducer(self,peer):
        self.producer=peer
        self.log.info('adding %s as producer',peer)
        print 'adding ',peer,' as producer'

    def failedProducer(self,peer):
        self.log.error('failed to add %s as producer',peer)
        print 'failed to add ',peer,' as producer'
        self.parent.streamComponent.stop()



    def stop(self):
        self.log.info('should stop')
        if not self.stopDefer:
            self.stopDefer=defer.Deferred()
            self.waitingToStop={}

        for k,ov in self.subOverlays.items():
            self.waitingToStop[k]=ov.stop()
            self.waitingToStop[k].addCallback(self.checkStop,k)
        return self.stopDefer


    def checkStop(self,ret,ov):
        if ov not in self.waitingToStop:
            raise KeyError("problem in check stop")

        del self.waitingToStop[ov]
        self.subOverlays[ov].purgeNS()
        del self.subOverlays[ov]

        if not self.waitingToStop:
            self.log.debug("all suboverlays stopped")
            print "all suboverlays stopped"
            self._stop()

    def _stop(self):
        self.log.info('stopping overlay')

        InformClientStoppedMessage.send(self.stream.id, self.server, self.controlPipe)
        try:
            InformClientStoppedMessage.send(self.stream.id, self.producer, self.controlPipe)
        except:
            pass


        self.stopDefer.callback(True)


    def returnNeighs(self,peer):
        ReturnNeighsMessage.send(self.stream.id,self.neighbours,peer,self.controlPipe)



    def toggleSwap(self,stop):
        for ov in self.subOverlays.values():
            ov.toggleSwap(stop)


    def getVizirStats(self):
        ret=(self.tempSwaps,time()-self.tempLastSwap,self.tempSatelites,time()-self.tempLastSatelite)
        self.tempSwaps=0
        self.tempSatelites=0
        return ret


    #because an overlay is supposed to have these methods
    def addNeighbour(self):
        pass

    def removeNeighbour(self):
        pass
