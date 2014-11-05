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
from messages.peerremovemessage import InformClientStoppedMessage,ClientDied
from messages.vizirmessages import *
from twisted.internet import task,reactor,defer
from random import choice,uniform
from bwmeasurement import FlowBwMeasurement
from subclient import SubOverlay
from superintersubclient import SuperInterOverlay
from baseintersubclient import BaseInterOverlay
from time import time
from cPickle import dumps
from p2ner.core.statsFunctions import counter, setLPB,setValue

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

        self.loopingCall=task.LoopingCall(self.checkAlive)
        self.loopingCall.start(1)
        self.statLoopingCall=task.LoopingCall(self.updateStats)
        self.statLoopingCall.start(1)

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
            self.subOverlays['super']=SubOverlay(self.swapFreq,superOverlay=True,interOverlay=False,_parent=self)
            self.subOverlays['superInter']=SuperInterOverlay(self.swapFreq,superOverlay=True,interOverlay=True,_parent=self)
        else:
            print "just a normal peer"
            self.subOverlays['base']=SubOverlay(self.swapFreq,superOverlay=False,interOverlay=False,_parent=self)
            self.subOverlays['baseInter']=BaseInterOverlay(self.swapFreq,superOverlay=False,interOverlay=True,_parent=self)


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

        self.loopingCall.stop()
        self.statLoopingCall.stop()

        self.stopDefer.callback(True)


    def returnNeighs(self,peer):
        ReturnNeighsMessage.send(self.stream.id,self.neighbours,peer,self.controlPipe)



    def toggleSwap(self,stop):
        for ov in self.subOverlays.values():
            ov.toggleSwap(stop)



    #because an overlay is supposed to have these methods
    def addNeighbour(self):
        pass

    def removeNeighbour(self):
        pass

    def checkAlive(self):
        for ov in self.subOverlays.values():
            for p in ov.getNeighbours():
                if time()-p.lastMessageTime>2:
                    ov.neighbourDead(p)
                    ClientDied.send(self.stream.id,[p],self.server,self.controlPipe)
                    ClientDied.send(self.stream.id,[p],self.producer,self.controlPipe)

    ######### VIZIR FUNCTIONS################
    def getVizirNeighbours(self):
        ret={}
        if self.superPeer:
            ret['0']=0
            ret['1']={}
            ret['1']['neighs']=[dumps(p) for p in self.subOverlays['super'].getNeighbours()]
            ret['1']['stats']=self.subOverlays['super'].getVizirStats()
            ret['1']['energy']=self.subOverlays['super'].getEnergy()

            ret['2']={}
            ret['2']['neighs']=[dumps(p) for p in self.subOverlays['superInter'].getNeighbours()]
            ret['2']['stats']=self.subOverlays['superInter'].getVizirStats()
            ret['2']['energy']=self.subOverlays['superInter'].getEnergy()
        else:
            ret['1']=0
            ret['0']={}
            ret['0']['neighs']=[dumps(p) for p in self.subOverlays['base'].getNeighbours()]
            ret['0']['stats']=self.subOverlays['base'].getVizirStats()
            ret['0']['energy']=self.subOverlays['base'].getEnergy()

            ret['2']={}
            ret['2']['neighs']=[dumps(p) for p in self.subOverlays['baseInter'].getNeighbours()]
            ret['2']['stats']=self.subOverlays['baseInter'].getVizirStats()
            ret['2']['energy']=self.subOverlays['baseInter'].getEnergy()

        return ret



    ############### stats ####################33
    def updateStats(self):
        en=self.getEnergy()
        setValue(self,"peerEnergy",en)
        setValue(self,'peerNeigh',len(self.getNeighbours()))

    def getEnergy(self):
        en=0
        for p in self.getNeighbours():
            if len(p.lastRtt):
                en +=sum(p.lastRtt)/len(p.lastRtt)
        return en


