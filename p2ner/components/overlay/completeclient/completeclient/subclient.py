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
from messages.submessages import *
from messages.validationmessages import *
from messages.peerremovemessage import ClientStoppedMessage
from twisted.internet import task,reactor,defer
from random import choice,uniform
from messages.swapmessages import *
from time import time,localtime
import networkx as nx
from p2ner.base.Peer import Peer
from p2ner.core.statsFunctions import counter,setValue
from hashlib import md5
from state import *
from swapException import SwapError

ASK_SWAP=0
ACCEPT_SWAP=1
LOCK_SENT=2
WAIT_SWAP=3
SEND_UPDATE=4
SEND_INIT_TABLE=5

CONTINUE=0
INSERT=1
REMOVE=2

class SubOverlay(Overlay):

    def registerMessages(self):
        self.messages = []
        self.messages.append(ClientStoppedMessage())
        self.messages.append(PeerListMessage())
        self.messages.append(AddNeighbourMessage())
        self.messages.append(AskSwapMessage())
        self.messages.append(RejectSwapMessage())
        self.messages.append(AcceptSwapMessage())
        self.messages.append(InitSwapTableMessage())
        self.messages.append(AskLockMessage())
        self.messages.append(AnswerLockMessage())
        self.messages.append(SwapPeerListMessage())
        self.messages.append(FinalSwapPeerListMessage())
        self.messages.append(SateliteMessage())
        self.messages.append(PingMessage())
        self.messages.append(PingSwapMessage())
        self.messages.append(SuggestNewPeerMessage())
        self.messages.append(SuggestMessage())
        self.messages.append(ConfirmNeighbourMessage())
        self.messages.append(AckUpdateMessage())
        self.messages.append(CleanSateliteMessage())
        self.messages.append(ValidateNeighboursMessage())
        self.messages.append(ReplyValidateNeighboursMessage())

    def initOverlay(self,swapFreq,superOverlay=True,interOverlay=False,**kwagrs):
        self.overlayType=10*int(superOverlay)+int(interOverlay)
        self.log=self.logger.getLoggerChild((str(self.overlayType)+'o'+str(self.stream.id)),self.interface)
        self.log.info('initing overlay'+str(self.overlayType))
        print 'initing overlay'+str(self.overlayType)
        self.sanityCheck(["stream", "control", "controlPipe"])

        self.registerMessages()

        self.superOverlay=superOverlay
        self.interOverlay=interOverlay
        self.subOverlay=self

        self.shouldStop=False
        self.stopDefer=None
        self.neighbours = []
        self.duringSwapNeighbours={}
        self.removeDuringSwap=[]
        self.partnerTable=[]
        self.satelite=0
        self.initiator=False
        self.passiveInitiator=False
        self.duringSwap=False
        self.pauseSwap=False

        self.swapFreq=swapFreq
        self.loopingCall = task.LoopingCall(self.startSwap)

        self.pingLoopingCall=task.LoopingCall(self.sendPing)
        self.pingLoopingCall.start(1)

        self.loopingCalls=[]
        self.loopingCalls.append(self.loopingCall)
        self.loopingCalls.append(self.pingLoopingCall)
        #needed for vizir stats
        self.tempSatelites=0
        self.tempSwaps=0
        self.tempLastSatelite=0
        self.tempLastSwap=0

        self.swapState={}
        self.enableSwap()
        self.askInitialNeighbours()


    def enableSwap(self):
        self.loopingCall.start(self.swapFreq)

    def askInitialNeighbours(self):
        AskInitNeighs.send(self.stream.id,self.superOverlay,self.interOverlay,self.server,self.controlPipe)

    def getNeighbours(self):
        return self.neighbours[:]


    def checkTriggerMessage(self,mSuperOverlay,mInterOverlay):
        if not mInterOverlay:
            return self.superOverlay==mSuperOverlay and self.interOverlay==mInterOverlay
        else:
            return self.superOverlay!=mSuperOverlay and self.interOverlay==mInterOverlay

    def checkTriggerInitiatorsMessage(self,mSuperOverlay,mInterOverlay):
        return self.superOverlay==mSuperOverlay and mInterOverlay==self.interOverlay


    ##################################################
    #ADDING NEIGH
    ##################################################

    #Initiator peer gets initial neighbor list. If he is not during swap he starts the adding producer
    def checkSendAddNeighbour(self,peer,originalPeer):
        peer.learnedFrom=originalPeer
        self.duringSwapNeighbours[peer]={}
        self.duringSwapNeighbours[peer]['INIT']=True
        if not self.duringSwap:
            self.log.debug('not during swap in check send add neighbour')
            self.sendAddNeighbour(peer)
        else:
            self.log.debug('during swap in check send add neighbour')

    #Initiator peer sends an add neighbour message to potential peer and sets an interrupt in case of failure
    def sendAddNeighbour(self,peer):
        if not self.isNeighbour(peer):
            inpeer,port=self.root.checkNatPeer()
            bw=min(65535,int(self.trafficPipe.callSimple('getReportedCap')))
            self.log.debug('sending addneighbour message to %s',peer)
            self.duringSwapNeighbours[peer]['CHECK']=reactor.callLater(5,self.checkAddNeigh,peer)
            AddNeighbourMessage.send(self.stream.id,self.superOverlay,self.interOverlay,port,bw,inpeer,peer,self.root.controlPipe)
        else:
            self.log.error('%s is yet in the overlay in send add neighbour',peer)
            self.duringSwapNeighbours.pop(peer)

    #Passive peer gets the initial message and if he is not under swap he continues. Otherwise he deferes the procedure until swap is over
    def checkAcceptNeighbour(self,peer):
        self.log.debug('in check accept neighbour for %s',peer)
        if not self.isNeighbour(peer):
            self.duringSwapNeighbours[peer]={}
            self.duringSwapNeighbours[peer]['INIT']=False
            if self.duringSwap:
                self.log.debug('during swap in check accept neighbour for %s',peer)
            else:
                self.acceptNeighbour(peer)
        else:
            self.log.error('%s is yet in the overlay in check accept neighbour',peer)

    #Passive peer accepts the invitation, adds initiator as neighbour and sends a confirmation message
    def acceptNeighbour(self,peer):
        if not self.isNeighbour(peer):
            self.neighbours.append(peer)
            self.log.info('adding %s to neighborhood',peer)
            print 'adding ',peer,' to neighborhood'
            ConfirmNeighbourMessage.send(self.stream.id,self.superOverlay,self.interOverlay, peer,self.controlPipe)
        else:
            self.log.error('In accept neighbour %s is already a neighbour',peer)
        self.duringSwapNeighbours.pop(peer)

    #Initiator peer get the confirmation and finally and the passive peer as neighbour
    def addNeighbour(self, peer):
        if self.duringSwap:
            self.log.error('during swap in addNeighbour')
        elif not self.isNeighbour(peer):
            self.neighbours.append(peer)
            self.log.info('adding %s to neighborhood',peer)
            print 'adding ',peer,' to neighborhood'
            PingMessage.send(peer,self.controlPipe)
        else:
            self.log.error("%s  yet in overlay" ,peer)

        try:
            self.duringSwapNeighbours[peer]['CHECK'].cancel()
            self.duringSwapNeighbours.pop(peer)
        except:
            self.log.error('new peer %s is not in during swap neighs %s',peer,self.duringSwapNeighbours)

    #if the interupt occurs means that the passive never answered so remove him from potential neighbours
    def checkAddNeigh(self,peer):
        self.log.error('in check add neigh for %s',peer)
        try:
            self.duringSwapNeighbours.pop(peer)
        except:
            self.log.error('cannot remove neigh from during swap neighbours')

    #when swap finishes answer any remaining neighbouring requests
    def addDuringSwapNeighbours(self):
        for peer,v in self.duringSwapNeighbours.items():
            if v['INIT'] and not self.shouldStop:
                self.sendAddNeighbour(peer)
            else:
                self.acceptNeighbour(peer)

    ########################### END INSERT ##################################


    def removeDuringSwapNeighbours(self):
        for p in self.removeDuringSwap:
            try:
                self.log.debug('removing %s after swap',p)
                self.neighbours.remove(p)
            except:
                self.log.error('could not remove %s after swap.Probably is not in the new table',p)

        self.removeDuringSwap=[]



    def removeNeighbour(self, peer):
        if self.duringSwap:
            self.removeDuringSwap.append(peer)

        try:
            self.neighbours.remove(peer)
        except:
            self.log.error('In remove neighbour %s is not a neighbor',peer)
            return

        self.log.info('removing %s from neighborhood',peer)
        print 'removing form neighbourhood ',peer

        if self.shouldStop:
            return

        if uniform(0,10)<5:
            self.log.info('should find a new neighbor')
            print 'should find a new neighbor'
            for p in self.neighbours:
                p.askedReplace=False
            self.findNewNeighbor()
        else:
            self.log.info('no further action needed')
            print 'no further action needed'

    def isNeighbour(self, peer):
        return peer in self.neighbours

    def stop(self):
        self.shouldStop=True
        self.log.info('should stop')
        if not self.stopDefer:
            self.stopDefer=defer.Deferred()
        reactor.callLater(0,self._stop)
        return self.stopDefer


    def _stop(self):
        self.log.error('should stop')
        if self.satelite or self.initiator or self.passiveInitiator:
            print 'can not stop '
            print 'satelite:',self.satelite
            print 'initiator:',self.initiator
            print 'passive initiator:',self.passiveInitiator
            return
        self.log.info('stopping overlay')

        #stop tasks
        for lcall in self.loopingCalls:
            try:
                lcall.stop()
            except:
                pass

        for n in self.getNeighbours():
            self.log.debug('sending clientStopped message to %s',n)
            ClientStoppedMessage.send(self.stream.id, self.superOverlay, self.interOverlay, n, self.controlPipe)
        self.log.error('stopping')
        self.stopDefer.callback(True)

    ###ACTIVE INITIATOR ##########################3

    def choosePassiveInitiatorPeer(self):
        return choice(self.neighbours)

    def checkValidNumNeighsForSwap(self):
        return len(self.neighbours)>1

    ### ASK SWAP
    def startSwap(self):
        self.log.debug('starting swap')
        if self.satelite or self.initiator or self.passiveInitiator or not self.checkValidNumNeighsForSwap() or self.shouldStop or len(self.duringSwapNeighbours) or self.pauseSwap:
            self.log.debug('no available conditions for swap %d,%d,%d,%d,%d',self.satelite,self.initiator,self.passiveInitiator,len(self.duringSwapNeighbours),len(self.neighbours))
            return

        ip=self.root.netChecker.localIp
        port=self.root.netChecker.controlPort

        m=md5()
        m.update(ip+str(port)+str(time()))
        h=m.hexdigest()
        h=h[:len(h)/8]
        swapid=int(h,16)


        self.initiator=True
        self.duringSwap=True
        peer=self.choosePassiveInitiatorPeer()

        self.swapState[swapid]={}
        self.swapState[swapid][ROLE]=INITIATOR
        self.swapState[swapid][STATE]=ASK_SWAP
        self.swapState[swapid][PARTNER]=peer
        check = reactor.callLater(3,self.checkStatus,swapid,peer)
        self.swapState[swapid][MSGS]={}
        self.swapState[swapid][MSGS][peer]=check

        self.passiveInitPeer=peer

        print 'sending askswap to:',peer,swapid
        self.log.warning('%s',self.getNeighbours())
        self.log.debug('sending ask swap message to %s %s'%(peer,swapid))
        AskSwapMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,peer,self.controlPipe)


    ###RECEIVED REJECT SWAP
    def recRejectSwap(self,peer,swapid):
        try:
            self.validateSwapMessage(peer,swapid,ASK_SWAP)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            self.cleanSwapState(swapid)
            return

        self.log.debug('swap was rejected from %s',peer)
        self.cleanSwapState(swapid)
        self.initiator=False
        self.duringSwap=False

    ###RECEIVED ACCEPT SWAP
    def recAcceptSwap(self,peer,peerlist,swapid):
        try:
            self.validateSwapMessage(peer,swapid,ASK_SWAP)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            self.cleanSwapState(swapid)
            return

        self.actionCompleted(swapid,peer)

        self.log.debug('swap accepted from %s',peer)

        self.tempSwaps +=1
        self.tempLastSwap=time()
        self.gotPartnerUpdatedTable=False
        self.partnerTable=peerlist
        for p in peerlist:                  ####should check it!!!!!!!!!!!!!!
            p.learnedFrom=peer
        self.sendTable(swapid)


    def getInitialSwapTable(self):
        neighs=[p for p in self.getNeighbours() if p!=self.passiveInitPeer]
        return neighs


    def sendTable(self,swapid):
        self.log.debug('sending initial routing table to passive initiator %s',self.passiveInitPeer)
        neighs=self.getInitialSwapTable()
        self.swapState[swapid][STATE]=WAIT_LOCKS_UTABLE
        self.swapState[swapid][MSGS]={}
        self.swapState[swapid][MSGS][self.passiveInitPeer]=reactor.callLater(4,self.checkStatus,swapid,self.passiveInitPeer)
        InitSwapTableMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,neighs,self.passiveInitPeer,self.controlPipe)
        self.sendLocks(swapid)

    def sendLocks(self,swapid):
        if self.initiator:
            pnode=self.passiveInitPeer
        else:
            pnode=self.initPeer

        self.log.debug('start sending locks')
        self.gotPartnerUpdatedTable=False
        availableNeighs=[p for p in self.partnerTable if p not in self.getNeighbours()]
        unavailableNeighs=[p for p in self.partnerTable if p in self.getNeighbours()]
        for p in unavailableNeighs:
            p.participateSwap=False
            p.partnerParticipateSwap=False
        for p in availableNeighs:
            self.log.debug('sending lock to %s',p)
            p.participateSwap=True
            p.partnerParticipateSwap=True
            p.waitLock=True
            self.log.debug('sending lock message for %s to %s'%(swapid,p))
            self.swapState[swapid][MSGS][p]=reactor.callLater(3,self.checkStatus,swapid,p)
            AskLockMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,[pnode],p,self.controlPipe)
        if not availableNeighs:
            self.log.debug('there are no locks to send')
            self.checkLockFinished(swapid)


    ###REICEVED LOCK ANSWER
    def recAnsLock(self,peer,lock,swapid):
        try:
            self.validateSateliteMessage(peer,swapid,WAIT_LOCKS_UTABLE)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            return

        self.actionCompleted(swapid,peer)

        self.log.debug('the lock answer from %s was %s',peer,lock)
        if not lock:
            peer.participateSwap=False
            peer.partnerParticipateSwap=False

        peer.waitLock=False
        self.checkLockFinished(swapid)


    def checkLockFinished(self,swapid):
        finished=True
        for p in self.partnerTable:
            if p.participateSwap and p.waitLock:
                finished=False
                break

        if finished:
            if self.initiator:
                if self.gotPartnerUpdatedTable:
                    self.performSwap(swapid)
            else:
                self.sendUpdatedSwapTable(swapid)

    ###RECEIVED UPDATED SWAP TABLE
    def recUpdatedSwapTable(self,peer,table,swapid):
        try:
            self.validateSwapMessage(peer,swapid,WAIT_LOCKS_UTABLE)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            return

        self.log.debug('got the updated swap table from passive %s',peer)
        self.gotPartnerUpdatedTable=True
        self.actionCompleted(swapid,peer)
        self.checkLockFinished(swapid)

    ###PERFORM SWAP

    def checkExecuteSwapTwice(self,initiatorTable,passiveTable):
        initActiveLength=len(initiatorTable)
        initPassiveLenght=len(passiveTable)
        initLength=initActiveLength+initPassiveLenght

        return initLength%2!=0


    def performSwap(self,swapid):
        self.swapState[swapid][STATE]=PERFORM_SWAP
        initialHoodEnergy=self.getCustomEnergy(self.getNeighbours())+self.getCustomPassiveEnergy(self.partnerTable)
        self.passiveInitPeer.participateSwap=False

        partnerSet=[p for p in self.getNeighbours() if p!=self.passiveInitPeer]
        availablePeers=[p for p in partnerSet+self.partnerTable if p.participateSwap or p.partnerParticipateSwap]

        for p in availablePeers:
            p.participateSwap=True

        execTwice=self.checkExecuteSwapTwice(partnerSet,self.partnerTable)

        if not execTwice:
            (newTable,newPartnerTable,energy)=self._performSwap(initialHoodEnergy,0)
            self.newTable=newTable
            self.newPartnerTable=newPartnerTable
        else:
            self.log.warning('executing swap twice')
            equal=False
            possibleSwaps={}
            for i in [0,1]:
                possibleSwaps[i]=self._performSwap(initialHoodEnergy,i)
            if int(10000*possibleSwaps[0][2])<int(10000*possibleSwaps[1][2]):
                choose=0
            elif int(10000*possibleSwaps[0][2])>int(10000*possibleSwaps[1][2]):
                choose=1
            else:
                equal=True
                if len(possibleSwaps[0][0])==len(self.getNeighbours()):
                    choose=0
                else:
                    choose=1

            (newTable,newPartnerTable,energy)=possibleSwaps[choose]
            self.newTable=newTable
            self.newPartnerTable=newPartnerTable
            self.log.warning('examin swap twice:%s %s %s %s %s %s %s %s %s %s %s \n'%(possibleSwaps[0][2],len(possibleSwaps[0][0]),len(possibleSwaps[0][1]),possibleSwaps[1][2],len(possibleSwaps[1][0]),len(possibleSwaps[1][1]),choose,equal,len(newTable),len(self.getNeighbours()),self.root.netChecker.localIp))

        finalHoodEnergy=self.getCustomEnergy(newTable)+self.getCustomPassiveEnergy(newPartnerTable)

        if int(1000*finalHoodEnergy)>int(1000*initialHoodEnergy) and len(self.neighbours)==len(newTable):
            self.log.error('major problem in swap')
            self.log.error('initial hood energy %s',initialHoodEnergy)
            self.log.error('final hood energy %s',finalHoodEnergy)
            print('initial hood energy %s',initialHoodEnergy)
            print('final hood energy %s',finalHoodEnergy)
        else:
            self.log.debug('initial hood energy %s',initialHoodEnergy)

        self.sendFinalTable(swapid)

    def calculateFinalTablesSizes(self,initiatorTable,passiveTable,bias):
        initActiveLength=len(initiatorTable)
        initPassiveLenght=len(passiveTable)
        initLength=initActiveLength+initPassiveLenght

        self.log.warning('initiatorSet:%s passiveSet:%s allSet:%s',initActiveLength,initPassiveLenght,initLength)

        if not bias:
            finalPassiveSet=int(initLength)/2
            finalActiveSet=initLength-finalPassiveSet
        else:
            finalActiveSet=int(initLength)/2
            finalPassiveSet=initLength-finalActiveSet

        return finalActiveSet,finalPassiveSet

    def _performSwap(self,initEnergy,bias=0):
        partnerSet=[p for p in self.getNeighbours() if p!=self.passiveInitPeer]
        availablePeers=[p for p in partnerSet+self.partnerTable if p.participateSwap or p.partnerParticipateSwap]

        finalActiveSet, finalPassiveSet=self.calculateFinalTablesSizes(partnerSet,self.partnerTable,bias)

        self.log.warning('finailinitiatorSet:%s finalpassiveSet:%s ',finalActiveSet,finalPassiveSet)

        activeUnavailablePeers=[p for p in partnerSet if not p.partnerParticipateSwap]
        passiveUnavailablePeers=[p for p in self.partnerTable if  not p.participateSwap]

        swapActiveLenght=finalActiveSet-len(activeUnavailablePeers)
        swapPassiveLenght=finalPassiveSet-len(passiveUnavailablePeers)
        swapLenght=swapActiveLenght+swapPassiveLenght

        self.log.warning('finalAtctiveSwapSet:%s finalPassiveSwapSet:%s ',swapActiveLenght,swapPassiveLenght)

        if (swapActiveLenght==0 and swapPassiveLenght==0) or (swapActiveLenght<0 or swapPassiveLenght<0):
            #swap finished
            newTable=self.getNeighbours()
            newPartnerTable=self.partnerTable
            self.log.warning('no point in performin swap')
            self.log.warning('passive init %s',self.passiveInitPeer)
            self.log.warning("current neughs %s",newTable[:])
            self.log.warning('partner table %s',self.partnerTable[:])
            self.log.warning('active unavailable %s',activeUnavailablePeers)
            self.log.warning('passive unavailable %s',passiveUnavailablePeers)
            finalHoodEnergy=self.getCustomEnergy(newTable)+self.getCustomPassiveEnergy(newPartnerTable)
            return (newTable,newPartnerTable,finalHoodEnergy)
        elif swapActiveLenght==0 and swapPassiveLenght!=0:
            newTable=self.constructFinalInitiatorTable(activeUnavailablePeers)
            newPartnerTable=passiveUnavailablePeers+availablePeers
            self.log.warning('all available peers goes to passive')

            self.log.warning("current neughs %s",self.getNeighbours())
            self.log.warning('partner table %s',self.partnerTable)
            self.log.warning('active unavailable %s',activeUnavailablePeers)
            self.log.warning('passive unavailable %s',passiveUnavailablePeers)
            self.log.warning('passive init %s',self.passiveInitPeer)
            self.log.warning('new final %s',newTable)
            self.log.warning('new passive final %s',newPartnerTable)
            finalHoodEnergy=self.getCustomEnergy(newTable)+self.getCustomPassiveEnergy(newPartnerTable)
            return (newTable,newPartnerTable,finalHoodEnergy)
        elif swapActiveLenght!=0 and swapPassiveLenght==0:
            self.log.warning('all available peers goes to passive')
            newTable=self.constructFinalInitiatorTable(activeUnavailablePeers+availablePeers)
            newPartnerTable=passiveUnavailablePeers
            self.log.warning('all available peers goes to active')

            self.log.warning("current neughs %s",self.getNeighbours())
            self.log.warning('partner table %s',self.partnerTable)
            self.log.warning('active unavailable %s',activeUnavailablePeers)
            self.log.warning('passive unavailable %s',passiveUnavailablePeers)
            self.log.warning('passive init %s',self.passiveInitPeer)
            self.log.warning('new final %s',newTable)
            self.log.warning('new passive final %s',newPartnerTable)
            finalHoodEnergy=self.getCustomEnergy(newTable)+self.getCustomPassiveEnergy(newPartnerTable)
            return (newTable,newPartnerTable,finalHoodEnergy)



        G=nx.DiGraph()
        G.add_node(-1,demand=-swapLenght)
        G.add_node(-2,demand=swapLenght)
        G.add_edge(-1,-3,capacity=swapActiveLenght)
        G.add_edge(-1,-4,capacity=swapPassiveLenght)
        temp={}
        count=0
        print 'swapActiveLenght:',swapActiveLenght
        print 'swapPassiveLenght:',swapPassiveLenght

        for p in availablePeers:
            rtt=0
            if len(p.lastRtt):
                rtt=sum(p.lastRtt)/len(p.lastRtt)
            else:
                self.log.error("can't perform swap with no rtt for %s",p)
                # raise ValueError("can't perform swap with no rtt for %s",p)

            temp[p]=count
            G.add_edge(-3,count,capacity=1,weight=int(1000*rtt))
            G.add_edge(-4,count,capacity=1,weight=int(1000*p.swapRtt))
            G.add_edge(count,-2,capacity=1)
            count +=1

        #flowDict=nx.min_cost_flow(G)

        try:
            flowDict=nx.min_cost_flow(G)
        except:
            raise ValueError('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
            for p in availablePeers:
                rtt=0
                if len(p.lastRtt):
                    rtt=sum(p.lastRtt)/len(p.lastRtt)
                print p,rtt,p.swapRtt
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print 'could not execute swap'
            sys.stderr.write('could not execute swapppppp %s\n'%self.root.netChecker.localIp)
            self.log.error("could not execute swap")
            newTable=self.getNeighbours()
            newPartnerTable=self.partnerTable
            self.log.warning("current neughs %s",newTable[:])
            self.log.warning('%s',self.getNeighbours())
            self.log.warning('partner table %s',self.partnerTable[:])
            finalHoodEnergy=self.getCustomEnergy(newTable)+self.getCustomPassiveEnergy(newPartnerTable)
            return (newTable,newPartnerTable,finalHoodEnergy)

        print flowDict
        #if flowDict['src']['active']!=swapActiveLenght or flowDict['src']['passive']!=swapPassiveLenght:
        #    raise ValueError('problem in perform swap')

        newActiveTable=[p for p in availablePeers if flowDict[-3][temp[p]]==1]
        newPassiveTable=[p for p in availablePeers if flowDict[-4][temp[p]]==1]

        if len(newActiveTable)+len(newPassiveTable)!=len(availablePeers):
            raise ValueError('problem in perform swap')
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print 'problem in perform swap'
            self.log.error('major problem in perform swap')
            self.log.error('number of available peers does not equal the sum of final tables\n.%d %d %d'%(len(availablePeers),len(newPassiveTable),len(newActiveTable)))
            print newActiveTable
            print newPassiveTable
            print availablePeers
            #reactor.stop()

        self.log.warning("current neughs %s",self.getNeighbours())
        self.log.warning('partner table %s',self.partnerTable)
        self.log.warning('active unavailable %s',activeUnavailablePeers)
        self.log.warning('new %s',newActiveTable)
        self.log.warning('passive unavailable %s',passiveUnavailablePeers)
        self.log.warning('new passive %s',newPassiveTable)
        newTable=self.constructFinalInitiatorTable(newActiveTable+activeUnavailablePeers)
        self.log.warning('passive init %s',self.passiveInitPeer)
        self.log.warning('new final %s',newTable)
        newPartnerTable=newPassiveTable+passiveUnavailablePeers
        self.log.warning('new passive final %s',newPartnerTable)

        finalHoodEnergy=self.getCustomEnergy(newTable)+self.getCustomPassiveEnergy(newPartnerTable)
        # if int(1000*initEnergy)<int(1000*finalHoodEnergy):
        #     self.log.error("%s %s"%(initEnergy,finalHoodEnergy))
        #     self.log.error('%s\n'%bias)
        #     n=[-1,-2]+range(count)+[-3,-4]
        #     for i in n:
        #         for j in n:
        #             if G.get_edge_data(i,j):
        #                 self.log.error('%s %s %s\n'%(i,j,G.get_edge_data(i,j)))
        #     self.log.error('%s\n'%temp)
        #     self.log.error('%s\n'%flowDict)
        return (newTable,newPartnerTable,finalHoodEnergy)

    def constructFinalInitiatorTable(self,table):
        return table+[self.passiveInitPeer]

    ###SENDING FINAL TABLE TO PASSIVE
    def sendFinalTable(self,swapid):
        self.log.debug('sending final swap table to %s',self.passiveInitPeer)
        for p in self.newPartnerTable:
            p.isNeighbour=True

        rem=[p for p in self.partnerTable if p not in self.newPartnerTable]
        for p in rem:
            p.isNeighbour=False

        FinalSwapPeerListMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,self.newPartnerTable+rem,self.passiveInitPeer,self.controlPipe)
        self.partnerPeer=self.passiveInitPeer
        self.updateSatelites(swapid)


    def updateSatelites(self,swapid):
        available=[p for p in self.newTable if p.participateSwap]
        self.log.warning('in update satelites')
        self.log.warning('new table:%s',self.newTable[:])
        self.log.warning('available:%s',available[:])


        con=[p for p in available if p in self.getNeighbours()]
        ins=[p for p in available if p not in self.getNeighbours()]
        rem=[p for p in self.getNeighbours() if p not in available and p.participateSwap and p!=self.partnerPeer]

        if not con+ins+rem:
            self.finishSwap(swapid)
            return

        self.checkDuplicates()

        self.swapState[swapid][STATE]=UPDATE_SATELITES
        inpeer,port=self.root.checkNatPeer()
        bw=min(65535,int(self.trafficPipe.callSimple('getReportedCap')))

        for p in con:
            p.swapAction=CONTINUE
            inform=None

            SateliteMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,p.swapAction,self.partnerPeer,inform,p,self.controlPipe)
            self.swapState[swapid][MSGS][p]=reactor.callLater(2,self.checkStatus,swapid,p)
            self.log.debug('sending update satelite to %s with action %s',p,p.swapAction)
            print 'sending update satelite to ',p,' with action ',p.swapAction

        for p in ins:
            inform={}
            inform['streamid']=self.stream.id
            inform['port']=port
            inform['bw']=bw
            inform['peer']=inpeer
            p.swapAction=INSERT

            SateliteMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,p.swapAction,self.partnerPeer,inform,p,self.controlPipe)
            self.swapState[swapid][MSGS][p]=reactor.callLater(2,self.checkStatus,swapid,p)
            self.log.debug('sending update satelite to %s with action %s',p,p.swapAction)
            print 'sending update satelite to ',p,' with action ',p.swapAction

        for p in rem:
            p.swapAction=REMOVE
            inform=None

            SateliteMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,p.swapAction,self.partnerPeer,inform,p,self.controlPipe)
            self.swapState[swapid][MSGS][p]=reactor.callLater(2,self.checkStatus,swapid,p)
            self.log.debug('sending update satelite to %s with action %s',p,p.swapAction)
            print 'sending update satelite to ',p,' with action ',p.swapAction

    def recAckUpdate(self,peer,swapid):
        self.log.debug('received ack update from %s for %d',peer,swapid)
        try:
            self.validateSateliteMessage(peer,swapid,UPDATE_SATELITES)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            self.cleanSwapState(swapid)
            return

        self.actionCompleted(swapid,peer)
        peer.participateSwap=False
        self.checkFinishSwap(swapid)

    def cleanSatelites(self,swapid):
        available=[p for p in self.newTable if p.participateSwap]
        self.log.warning('in clean satelites')
        if not available:
            self.finishSwap(swapid)
            return

        inpeer,port=self.root.checkNatPeer()
        bw=min(65535,int(self.trafficPipe.callSimple('getReportedCap')))

        for p in available:
            p.participateSwap=False
            p.swapAction=CONTINUE
            inform=None
            CleanSateliteMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,p.swapAction,self.partnerPeer,inform,p,self.controlPipe)
            self.log.debug('sending clean update satelite to %s',p)
            print 'sending clean update satelite to ',p,' with action ',p.swapAction


        self.cleanSwapState(swapid)

        self.initiator=False
        self.passiveInitiator=False
        self.duringSwap=False
        self.swapState.pop(swapid)
        self.addDuringSwapNeighbours()
        if self.shouldStop:
            self._stop()

    def checkFinishSwap(self,swapid):
        self.log.debug('in check swap finish for %d',swapid)
        self.log.debug('%s',self.swapState[swapid][MSGS])
        if not len(self.swapState[swapid][MSGS]):
            self.finishSwap(swapid)

    def finishSwap(self,swapid):
        self.log.info('swap with %s finished',self.partnerPeer)
        self.log.info('old table %s',self.getNeighbours())
        print '---------------------------'
        print 'SWAP FINISHED'
        print '------------------------------'
        print 'old table'
        print self.getNeighbours()
        en=self.getEnergy()
        self.log.info('old energy %f',en)
        print 'with energy:',en
        print 'new table'
        print self.newTable
        self.neighbours=self.newTable
        self.log.info('new table %s',self.newTable[:])
        en=self.getEnergy()
        print 'with energy:',en
        self.log.info('new energy %f',en)
        self.initiator=False
        self.passiveInitiator=False
        self.duringSwap=False
        self.checkDuplicates()
        self.swapState.pop(swapid)
        self.addDuringSwapNeighbours()
        self.removeDuringSwapNeighbours()
        if self.shouldStop:
            self._stop()

    ###PASSIVE INITIATOR##############################

    ###RECEIVED ASK SWAP
    def checkValidInitiator(self,peer):
        return peer in self.getNeighbours()

    def getInitialPassiveTable(self,peer):
        neighs=[n for n in self.getNeighbours() if n!=peer]
        return neighs


    def recAskSwap(self,peer,swapid):
        self.log.debug('received ask swap from %s',peer)
        print 'received ask swap from ',peer
        if not self.checkValidInitiator(peer):
            self.log.error('he is not my neighbor so rejecting the swap') ####need to chnage and take action
            RejectSwapMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,peer,self.controlPipe)
            return
        if swapid in self.swapState:
            self.log.error('got a request for an already existing swapid \nState:%s\npeer:%s,swapid:%s'%(self.swapState,peer,swapid))
            return
        if self.satelite or self.initiator or self.passiveInitiator or self.shouldStop or len(self.duringSwapNeighbours) or self.pauseSwap:
            RejectSwapMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,peer,self.controlPipe)
            self.log.debug('and rejected it %d,%d,%d,%d',self.satelite,self.initiator,self.passiveInitiator,len(self.duringSwapNeighbours))
        else:
            counter(self,'swapInitiators')
            self.log.debug('and accepted it')

            self.tempSwaps+=1
            self.tempLastSwap=time()

            self.passiveInitiator=True
            self.initPeer=peer
            self.duringSwap=True
            neighs=self.getInitialPassiveTable(peer)
            self.swapState[swapid]={}
            self.swapState[swapid][ROLE]=PASSIVE
            self.swapState[swapid][PARTNER]=peer
            self.swapState[swapid][STATE]=WAIT_INIT_TABLE
            self.swapState[swapid][MSGS]={}
            self.swapState[swapid][MSGS][peer] =reactor.callLater(2,self.checkStatus,swapid,peer)
            AcceptSwapMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,neighs,peer,self.controlPipe)


    ###RECEIVED INITIAL SWAP ROUTING TABLE
    def recInitSwapTable(self,peer,peerlist,swapid):
        try:
            self.validateSwapMessage(peer,swapid,WAIT_INIT_TABLE)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            self.cleanSwapState(swapid)
            return

        self.log.debug('received initial swap routing table from %s',peer)

        self.actionCompleted(swapid,peer)
        self.swapState[swapid][STATE]=WAIT_LOCKS_UTABLE

        self.partnerTable=peerlist
        for p in peerlist:  ###should check if this is needed!!!!!!!!!!!!!!!!!!
            p.learnedFrom=peer
        self.sendLocks(swapid)

    ###SEND UPDATE SWAP TABLE
    def sendUpdatedSwapTable(self,swapid):
        self.log.debug('sending updated passive table to active initiator %s',self.initPeer)
        self.log.debug('%s',self.partnerTable[:])
        self.swapState[swapid][STATE]=WAIT_FINAL_TABLE
        self.swapState[swapid][MSGS][self.initPeer]=reactor.callLater(5,self.checkStatus,swapid,self.initPeer)
        SwapPeerListMessage.send(self.stream.id,self.superOverlay,self.interOverlay, swapid, self.partnerTable, self.initPeer, self.controlPipe)


    ###RECEIVED FINAL SWAP TABLE
    def recFinalSwapTable(self,peer,table,swapid):
        try:
            self.validateSwapMessage(peer,swapid,WAIT_FINAL_TABLE)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            return

        self.actionCompleted(swapid,peer)
        self.log.debug('received final swap table from %s',self.initPeer)
        self.log.info('%s',table)
        self.newTable=[p for p in table if p.isNeighbour]
        self.log.info('%s',self.newTable)
        self.initPeer.participateSwap=False
        self.newTable=self.constructFinalPassiveTable(self.newTable)
        self.partnerPeer=self.initPeer
        for p in table:
            p.participateSwap=p.partnerParticipateSwap
        self.updateSatelites(swapid)

    def constructFinalPassiveTable(self,table):
        return table+[self.initPeer]

    ###SATELITES ########################################

    def recAskLock(self,peer,partner,swapid):
        if swapid in self.swapState:
            self.log.error('got an ask lock for an already existing swap')
            self.log.error('peer:%s,partner:%s,swapid:%s,swapState:%s'%(peer,partner,swapid,self.swapState))
            return

        self.log.debug('received ask lock for %s from %s'%(swapid,peer))
        print 'received ans lock from ',peer
        if self.initiator or self.passiveInitiator or self.shouldStop:
            AnswerLockMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,False,peer,self.controlPipe)
            self.log.debug('and rejected it')
            print 'and rejected it'
        elif peer in self.getNeighbours() or partner not in self.getNeighbours():
            AnswerLockMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,False,peer,self.controlPipe)
            self.log.error('received ask lock for a wrong set of peers for %d',swapid)
            self.log.error('peer:%s partner:%s neighbours:%s',peer,partner,self.getNeighbours())
        else:
            self.swapState[swapid]={}
            self.swapState[swapid][ROLE]=SATELITE
            self.swapState[swapid][ORIGINATOR]=peer
            self.swapState[swapid][PARTNER]=partner
            self.swapState[swapid][MSGS]={}
            self.swapState[swapid][STATE]=WAIT_UPDATE
            self.swapState[swapid][MSGS][peer]=reactor.callLater(5,self.checkStatus, swapid,peer)
            self.swapState[swapid][MSGS][partner]=reactor.callLater(5,self.checkStatus, swapid,partner)

            peer.lockPartner=partner
            counter(self,'swapSatelites')

            self.satelite+=2
            self.tempSatelites+=1
            self.tempLastSatelite=time()

            AnswerLockMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,True,peer,self.controlPipe)
            self.log.debug('and accepted it %s'%swapid)



    def recUpdateSatelite(self,peer,action,partner,swapid,ack=True):
        self.log.debug('received update satelite from %s with partner %s for %s',peer,partner,swapid)

        try:
            self.validateUpdateMessage(peer,action,partner,swapid,WAIT_UPDATE)
        except SwapError as e:
            print 'errorrrr'
            print e.message
            print e.peer
            print e.swapSnapshot
            #should do clean up work
            return

        print 'received update satelite from ',peer,' with partner ',partner,' and action ',action
        if action==CONTINUE:
            self.log.debug('with action continue')
            action=self.swapState[swapid][MSGS].pop(partner)
            action.cancel()
            action=self.swapState[swapid][MSGS].pop(peer)
            action.cancel()
            self.swapState.pop(swapid)
            self.satelite -=2
        elif action==INSERT:
            self.log.debug('with action insert %s',peer)
            self.neighbours.append(peer)
            self.satelite -=1
            self.actionCompleted(swapid,peer)
            if not partner in self.swapState[swapid][MSGS]:
                self.swapState.pop(swapid)
        else:
            self.log.debug('with action remove %s',peer)
            self.neighbours.remove(peer)
            self.actionCompleted(swapid,peer)
            self.satelite -=1
            if not partner in self.swapState[swapid][MSGS]:
                self.swapState.pop(swapid)

        if ack:
            self.log.debug('sending ack update message to %s',peer)
            AckUpdateMessage.send(self.stream.id,self.superOverlay,self.interOverlay,swapid,peer,self.controlPipe)

        self.log.info('satelite %d',self.satelite)
        self.log.info('table %s',self.getNeighbours())
        if self.satelite<0:
            self.log.error('negative value of satelite')
            print 'negative value of satelite'
            self.satelite=0
            #reactor.stop()
        if self.initiator or self.passiveInitiator or self.duringSwap:
            self.log.error('got update satelite while in swap')
            print 'got update satelite while in swap'
            print self.initiator,self.passiveInitiator, self.duringSwap
            print peer,partner,action
            #reactor.stop()
        if not self.satelite and self.shouldStop:
            self._stop()


    def checkStatus(self,swapid,peer):
        status=self.swapState[swapid][STATE]
        if status==ASK_SWAP:
            self.swapState.pop(swapid)
            self.initiator=False
            self.passiveInitPeer=None
            self.duringSwap=False
            self.log.error('never got an answer for ask swap from %s for %d',peer,swapid)
            print 'ask swap to ',peer,'failed'
        elif status==WAIT_LOCKS_UTABLE:
            if peer==self.passiveInitPeer:
                self.log.error('initial swap routing table delivery to %s failed for %d',peer,swapid)
                self.initiator=False
                self.duringSwap=False
                self.cleanSatelites(swapid)
            else:
                self.log.error('Ask lock to %s failed for %d',peer,swapid)
                peer.participateSwap=False
                peer.partnerParticipateSwap=False
                self.swapState[swapid][MSGS].pop(peer)
                self.checkLockFinished(swapid)
        elif status==WAIT_INIT_TABLE:
            self.log.error('send accept failed')
            self.cleanSwapState(swapid)
            self.passiveInitiator=False
            self.duringSwap=False
        elif status==WAIT_FINAL_TABLE:
            self.duringSwap=False
            self.passiveInitiator=False
            self.log.error('send updated table to %s failedf for %d',peer,swapid)
            setValue(self,'log','send updated table to %s failed')
            self.cleanSatelites(swapid)
        elif status==WAIT_UPDATE:
            self.swapState[swapid][MSGS].pop(peer)
            self.satelite -=1
            self.log.error('never received update satelite from %s for %d',peer,swapid)
        elif status==UPDATE_SATELITES:
            self.log.error('failed to update satelite %s for %d',peer,swapid)
            self.log.info('removing %s from swap table',peer)
            self.swapState[swapid][MSGS].pop(peer)
            try:
                self.newTable.remove(peer)
            except:
                self.log.error('in check status UPDATE_SATELITES cannot remove %s for %d. Probably the action was REMOVE',peer,swapid)
            self.checkFinishSwap(swapid)
        else:
            self.log.error('Unknown STATUSSSSSSSS %s'%status)


    ############## ENERGY FUNCTIONS ###############################
    def getEnergy(self):
        en=0
        for p in self.neighbours:
            if len(p.lastRtt):
                en +=sum(p.lastRtt)/len(p.lastRtt)
        return en

    def getCustomEnergy(self,table):
        en=0
        for p in table:
            if len(p.lastRtt):
                en +=sum(p.lastRtt)/len(p.lastRtt)
        return en

    def getCustomPassiveEnergy(self,table):
        en=0
        for p in table:
            en +=p.swapRtt
        return en


    ################ REPLACE REMOVED NEIGHBOUR ALGORITHM ##################################
    def findNewNeighbor(self):
        neighs=[p for p in self.neighbours if not p.askedReplace]
        if len(neighs):
            askNeigh=choice(neighs)
            SuggestNewPeerMessage.send(self.stream.id,self.superOverlay,self.interOverlay,self.getNeighbours(),askNeigh,self.controlPipe,err_func=self.sendFindNewFailed)
        else:
            self.log.debug("there isn't an appropiate neighbour for asking for a new peer\n Contacting Server")
            print "there isn't an appropiate neighbour for asking for a new peer\n Contacting Server"
            SuggestNewPeerMessage.send(self.stream.id,self.superOverlay,self.interOverlay,self.getNeighbours(),Peer(self.stream.server[0],self.stream.server[1]),self.controlPipe)
            pass

    def sendFindNewFailed(self,peer):
        self.log.warning('find new neighbor message to %s failed',peer)
        setValue(self,'log','find new neighbor message failed')
        peer.askedReplace=True
        self.findNewNeighbor()

    def suggestNewPeer(self,peer,neighs):
        avNeighs=[p for p in self.neighbours if p!=peer and p not in neighs]
        SuggestMessage.send(self.stream.id,self.superOverlay,self.interOverlay,avNeighs,peer,self.controlPipe)

    def availableNewPeers(self,peer,avNeighs):
        avNeighs=[p for p in avNeighs if p not in self.neighbours]
        if not len(avNeighs):
            peer.askedReplace=True
            if peer!=Peer(self.stream.server[0],self.stream.server[1]):
                self.findNewNeighbor()
            else:
                self.log.warning('there are no new peers to connect to')
                print 'there are no new peers to connect to'
            return

        newPeer=choice(avNeighs)
        self.log.debug('received available peers message from %s with %s',peer,newPeer)
        self.checkSendAddNeighbour(newPeer,peer)





    ################## SWAP HELPER FUNCTIONS #################################
    def checkDuplicates(self):
        neighs=self.getNeighbours()
        if len(neighs)!=len(set(neighs)):
            self.log.error('duplicate in table after swap\n%s'%neighs)
            print 'DUPLICATESSSSSSSSSSSSSSSSSSSSSS'
            print neighs
            #reactor.stop()


    def validateSwapMessage(self,peer,swapid,state):
        self._validateAllMessage(peer,swapid,state)
        if peer!=self.swapState[swapid][PARTNER]:
            self._logValidationError(peer,swapid,state)
            self.log.error('Received swap message from wrong peer')
            self.log.error('received from :%s'%peer)
            self.log.error('expected from:%s'%self.swapState[swapid][PARTNER])
            raise SwapError('Received swap message from wrong peer',peer,swapid,state,self.swapState)
        if self.swapState[swapid][ROLE]==INITIATOR and self.swapState[swapid][PARTNER]!=self.passiveInitPeer:
            self._logValidationError(peer,swapid,state)
            self.log.error('passive initiator is not the same in state and variable %s %s'%(self.swapState[swapid][PARTNER],self.passiveInitPeer))
            raise SwapError('passive initiator is not the same in state and variable',peer,swapid,state,self.swapState)
        if self.swapState[swapid][ROLE]==PASSIVE and self.swapState[swapid][PARTNER]!=self.initPeer:
            self._logValidationError(peer,swapid,state)
            self.log.error('initiator is not the same in state and variable %s %s'%(self.swapState[swapid][PARTNER],self.initPeer))
            raise SwapError('passive initiator is not the same in state and variable',peer,swapid,state,self.swapState)

    def validateSateliteMessage(self,peer,swapid,state):
        self._validateAllMessage(peer,swapid,state)
        if peer not in self.swapState[swapid][MSGS]:
            self._logValidationError(peer,swapid,state)
            self.log.error('received satelite message from a wrong peer')
            raise SwapError('received satelite message from a wrong peer',peer,swapid,state,self.swapState)
        if state==WAIT_LOCKS_UTABLE and not peer.participateSwap:
            self._logValidationError(peer,swapid,state)
            self.log.error('received satelite message from a none participating peer')
            raise SwapError('received satelite message from a non participating peer',peer,swapid,state,self.swapState)
        if state==UPDATE_SATELITES and not peer.participateSwap:
            self._logValidationError(peer,swapid,state)
            self.log.error('received ackUpdate satelite message from a none participating peer')
            raise SwapError('received ackUpdate satelite message from a non participating peer',peer,swapid,state,self.swapState)


    def _validateAllMessage(self,peer,swapid,state):
        if swapid not in self.swapState:
            self._logValidationError(peer,swapid,state)
            self.log.error('Received message for an unknown swap')
            raise SwapError('Received message for an unknown swap',peer,swapid,state,self.swapState)
        if state!=self.swapState[swapid][STATE]:
            self._logValidationError(peer,swapid,state)
            self.log.error('Received swap message for a wrong state %s %s'%(state,self.swapState[swapid][STATE]))
            raise SwapError('Received swap message for a wrong state',peer,swapid,state,self.swapState)

    def _logValidationError(self,peer,swapid,state):
        self.log.error('error in validating swap message from %s for %d',peer,swapid)
        self.log.error('swapState:%s'%self.swapState)
        self.log.error('message from:%s,swapId:%s,expecting state:%s'%(peer,swapid,state))

    def validateUpdateMessage(self,peer,action,partner,swapid,state):
        self._validateAllMessage(peer,swapid,state)

        ##check if message is form the right peer
        if action==CONTINUE :
            neigh=peer
            other=partner
        elif action==INSERT:
            neigh=partner
            other=peer
        else:
            neigh=peer
            other=partner

        if self.swapState[swapid][ORIGINATOR]!=other or self.swapState[swapid][PARTNER]!=neigh:
            self.log.error('got update satelite for wrong set of peers')
            self.log.error('expecting from %s,%s got from %s %s'%(self.swapState[swapid][ORIGINATOR],self.swapState[swapid][PARTNER],other,neigh))
            raise SwapError('Received update message from wrong set of peers',peer,swapid,state,self.swapState)


        ##check peers in satelite's table
        if action==CONTINUE:
            neigh=[peer]
            notNeigh=[]  #should be partner but there is a problem with during swap neighbours
        elif action==INSERT:
            notNeigh=[peer]
            neigh=[]
        else:
            neigh=[peer]
            notNeigh=[]

        for n in neigh:
            if n not in self.getNeighbours():
                self.log.error('in update message with action %s: %s should be my neighbour but it is not'%(action,n))
                raise SwapError('in update message. Peer is not my neighbor',peer,swapid,state,self.swapState)

        for n in notNeigh:
            if n in self.getNeighbours():
                self.log.error('in update message with action %s: %s should not be my neighbour but it is'%(action,n))
                raise SwapError('in update message. Peer is already my neighbor',peer,swapid,state,self.swapState)


    def cleanSwapState(self,swapid):
        try:
            temp=self.swapState.pop(swapid)
            for v in temp[MSGS].values():
                v.cancel()
        except:
            self.log.error('swapid:%d not in swap state:%s in cleanSwapState',swapid,self.swapState)

    def actionCompleted(self,swapid,peer):
        action=self.swapState[swapid][MSGS].pop(peer)
        action.cancel()
        return len(self.swapState[swapid][MSGS])




    ##################### VIZIR HELPER FUNCTIONS ###################################
    def validateNeighbours(self):
        if self.duringSwap or self.satelite or len(self.duringSwapNeighbours) or len(self.removeDuringSwap):
            self.log.error('not in a clean state')
            self.log.error('during swap:%s',self.duringSwap)
            self.log.error('satelite:%s',self.satelite)
            self.log.error('during swap neighbours:%s',self.duringSwapNeighbours)
            self.log.error('during swap remove neighbours:%s',self.removeDuringSwap)
        for p in self.getNeighbours():
            self.log.debug('send validate message to %s',p)
            p.checked=False
            ValidateNeighboursMessage.send(self.stream.id,self.superOverlay, self.interOverlay, p,self.controlPipe)
        reactor.callLater(2,self.checkFinishValidation)

    def ansValidateNeighs(self,peer):
        ans=peer in self.getNeighbours()
        ReplyValidateNeighboursMessage.send(self.stream.id,self.superOverlay, self.interOverlay, ans,peer,self.controlPipe)
        if not ans:
            self.log.error('%s is not my neighbor',peer)

    def checkValidateNeighs(self,ans,peer):
        if not ans:
            self.log.error('i am not a neighbour to %s',peer)
        else:
            peer.checked=True
            self.log.debug('everything is ok with %s',peer)
        notChecked=[p for p in self.getNeighbours() if not p.checked]
        if not notChecked:
            self.log.error('validation finished and everything is excellent')

    def checkFinishValidation(self):
        for p in self.getNeighbours():
            if not p.checked:
                self.log.error('problem in validating %s',p)

    def returnNeighs(self,peer):
        ReturnNeighsMessage.send(self.stream.id,self.neighbours,peer,self.controlPipe)


    def getVizirStats(self):
        ret=(self.tempSwaps,time()-self.tempLastSwap,self.tempSatelites,time()-self.tempLastSatelite)
        self.tempSwaps=0
        self.tempSatelites=0
        return ret

    def toggleSwap(self,stop):
        self.log.debug('in toggle swap.Pause is %s',stop)
        self.pauseSwap=stop
        if self.pauseSwap:
            reactor.callLater(4,self.validateNeighbours)

    ################ PING MESSAGES FOR UNGRACEFUL DEPARTURES ######################3
    def sendPing(self):
        try:
            running=self.scheduler.running
        except:
            return
        if not running:
            for p in self.getNeighbours():
                PingSwapMessage.send(p,self.controlPipe)
