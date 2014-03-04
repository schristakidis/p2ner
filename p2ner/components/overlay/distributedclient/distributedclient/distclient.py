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
from messages.peerlistmessage import *
from messages.peerremovemessage import ClientStoppedMessage
from twisted.internet import task,reactor,defer
from random import choice,uniform
from messages.swapmessages import *
from time import time
import networkx as nx
from p2ner.base.Peer import Peer
from p2ner.core.statsFunctions import counter,setValue

ASK_SWAP=0
ACCEPT_SWAP=1
LOCK_SENT=2
WAIT_SWAP=3
SEND_UPDATE=4
SEND_INIT_TABLE=5

CONTINUE=0
SUBSTITUTE=1
DUMMY_SUBSTITUTE=2

class DistributedClient(Overlay):

    def registerMessages(self):
        self.messages = []
        self.messages.append(PeerListMessage())
        self.messages.append(ClientStoppedMessage())
        self.messages.append(PeerListPMessage())
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
        self.messages.append(GetNeighsMessage())
        self.messages.append(SuggestNewPeerMessage())
        self.messages.append(SuggestMessage())
        self.messages.append(ConfirmNeighbourMessage())
        self.messages.append(PingSwapMessage())

    def initOverlay(self):
        self.log=self.logger.getLoggerChild(('o'+str(self.stream.id)),self.interface)
        self.log.info('initing overlay')
        print 'initing overlay'
        self.sanityCheck(["stream", "control", "controlPipe"])

        self.shouldStop=False
        self.stopDefer=None
        self.registerMessages()
        self.neighbours = []
        self.duringSwapNeighbours=[]
        self.tempNeighs=[]
        self.partnerTable=[]
        self.satelite=0
        self.initiator=False
        self.passiveInitiator=False
        self.duringSwap=False
        self.numNeigh=self.stream.overlay['numNeigh']
        self.loopingCall = task.LoopingCall(self.startSwap)
        self.loopingCall.start(self.stream.overlay['swapFreq'])
        self.statsLoopingCall=task.LoopingCall(self.collectStats)
        self.statsLoopingCall.start(2)
        self.pingCall=task.LoopingCall(self.sendPing)
        self.pingCall.start(1)

        self.tempSatelites=0
        self.tempSwaps=0
        self.tempLastSatelite=0
        self.tempLastSwap=0

        self.tempPossibleNeighs=[]
        AskInitNeighs.send(self.stream.id,self.server,self.controlPipe)

    def getNeighbours(self):
        return self.neighbours[:]

    def sendAddNeighbour(self,peer,originalPeer):
        inpeer,port=self.root.checkNatPeer()
        #self.log.info('my details %s port:%d',inpeer,port)
        bw=int(self.trafficPipe.callSimple('getBW')/1024)
        peer.learnedFrom=originalPeer
        self.tempPossibleNeighs.append(peer)
        AddNeighbourMessage.send(self.stream.id,port,bw,inpeer,peer,self.root.controlPipe)

    def addNeighbour(self, peer,temp=True):
        if not self.isNeighbour(peer):
            #if self.netChecker.nat and peer.ip==self.netChecker.externalIp:
             #   peer.useLocalIp=True
            if self.duringSwap:
                self.duringSwapNeighbours.append(peer)
                self.log.info('adding %s to during swap neighborhood',peer)
                print 'eeeeeeeeeeeeeeeeeeeeeee'
                print 'during swap neighbour ',peer
            else:
                self.neighbours.append(peer)
                self.log.info('adding %s to neighborhood',peer)
                print 'adding ',peer,' to neighborhood'
            PingMessage.send(peer,self.controlPipe)
        else:
            self.log.error("%s  yet in overlay" ,peer)
            #raise ValueError("%s peer yet in overlay" % str(peer))
            setValue(self,'log','peer yet in overlay')
        print '--------------------'
        print 'NEW NEIGH'
        for p in self.neighbours:
            print p,p.useLocalIp,p.lip
            print p.reportedBW

        if temp:
            try:
                self.tempPossibleNeighs.remove(peer)
            except:
                self.log.error('new peer %s is not in temp neighs %s',peer,self.tempPossibleNeighs)


    #def failedNeighbour(self,peer):
     #   self.log.warning('failed to add %s to neighborhood',peer)
     #   print 'failed to add ',peer,' to neighbourhood'
      #  setValue(self,'log','failed to add peer to neighbourhood')

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
            if uniform(0,10)<5:
                self.log.info('should find a new neighbor')
                print 'should find a new neighbor'
                for p in self.neighbours:
                    p.askedReplace=False
                self.findNewNeighbor()
            else:
                self.log.info('no further action needed')
                print 'no further action needed'
        except:
            self.log.error('%s is not a neighbor',peer)
            setValue(self,'log','peer to remove is not a neighbor')

    def isNeighbour(self, peer):
        return peer in self.neighbours

    def stop(self):
        self.shouldStop=True
        self.log.warning('should stop')
        if not self.stopDefer:
            self.stopDefer=defer.Deferred()
        reactor.callLater(0,self._stop)
        return self.stopDefer


    def _stop(self):
        if self.satelite or self.initiator or self.passiveInitiator:
            print 'can not stop '
            print 'satelite:',self.satelite
            print 'initiator:',self.initiator
            print 'passive initiator:',self.passiveInitiator
            return
        self.log.info('stopping overlay')
        self.log.debug('sending clientStopped message to %s',self.server)
        try:
            self.loopingCall.stop()
        except:
            pass
        try:
            self.statsLoopingCall.stop()
        except:
            pass
        for p in self.neighbours:
            try:
                p.checkResponse.cancel()
            except:
                pass
        if self.duringSwap:
            for p in self.partnerTable:
                try:
                    p.checkRespone.cancel()
                except:
                    pass
        ClientStoppedMessage.send(self.stream.id, self.server, self.controlPipe)
        ClientStoppedMessage.send(self.stream.id, self.producer, self.controlPipe)
        for n in self.getNeighbours():
            self.log.debug('sending clientStopped message to %s',n)
            ClientStoppedMessage.send(self.stream.id, n, self.controlPipe)
        self.stopDefer.callback(True)

    ###ACTIVE INITIATOR ##########################3

    ### ASK SWAP
    def startSwap(self):
        self.log.debug('starting swap')
        if self.satelite or self.initiator or self.passiveInitiator or len(self.neighbours)<=1 or self.shouldStop:
            self.log.debug('no available conditions for swap %d,%d,%d,%d',self.satelite,self.initiator,self.passiveInitiator,len(self.neighbours))
            return

        self.initiator=True
        peer=choice(self.neighbours)
        self.log.warning('%s',self.getNeighbours())
        self.log.debug('sending ask swap message to %s',peer)
        AskSwapMessage.send(self.stream.id,peer,self.controlPipe,err_func=self.askFailed,suc_func=self.askReceived)

    def askFailed(self,peer):
        self.log.error('ask swap to %s failed',peer)
        print 'ask swap to ',peer,'failed'
        setValue(self,'log','ask swap failed')
        self.initiator=False

    def askReceived(self,peer):
        counter(self,'swapInitiators')
        self.passiveInitPeer=peer
        self.passiveInitPeer.checkResponse= reactor.callLater(3,self.checkStatus,ASK_SWAP,peer)


    ###RECEIVED REJECT SWAP
    def recRejectSwap(self,peer):
        if peer!=self.passiveInitPeer:
            #raise ValueError('problem in receive reject swap. Rejecting peer is not the passive initiator')
            self.log.error('problem in receive reject swap. Rejecting peer %s is not the passive initiator %s',peer,self.passiveInitPeer)
            print 'problem in receive reject swap. Rejecting peer is not the passive initiator'
            setValue(self,'log','problem in receive reject swap. Rejecting peer is not the passive initiator')
            #reactor.stop()
        self.log.debug('swap was rejected from %s',peer)
        peer.checkResponse.cancel()
        self.initiator=False

    ###RECEIVED ACCEPT SWAP
    def recAcceptSwap(self,peer,peerlist):
        if peer!=self.passiveInitPeer:
            #raise ValueError('problem in receive accept swap. Accepting peer is not the passive initiator')
            self.log.error('problem in receive accept swap. Accepting peer %s is not the passive initiator %s',peer,self.passiveInitPeer)
            print 'problem in receive accept swap. Accepting peer is not the passive initiator'
            setValue(self,'log','problem in receive accept swap. Accepting peer is not the passive initiator')
            #reactor.stop()
        peer.checkResponse.cancel()
        self.log.debug('swap accepted from %s',peer)
        print 'swap accepted from ',peer

        self.tempSwaps +=1
        self.tempLastSwap=time()
        self.duringSwap=True
        self.gotPartnerUpdatedTable=False
        self.partnerTable=peerlist
        for p in peerlist:                  ####should check it!!!!!!!!!!!!!!
            p.learnedFrom=peer
        self.sendTable()


    def sendTable(self):
        self.log.debug('sending initial routing table to passive initiator %s',self.passiveInitPeer)
        neighs=[n for n in self.getNeighbours()]
        neighs.remove(self.passiveInitPeer)
        InitSwapTableMessage.send(self.stream.id,neighs,self.passiveInitPeer,self.controlPipe,err_func=self.sendTableFailed,suc_func=self.sendTableSuccess)

    def sendTableSuccess(self,peer):
        self.log.debug('initial table sent was succesful to %s',peer)
        self.sendLocks()
        peer.checkResponse=reactor.callLater(5,self.checkStatus,SEND_INIT_TABLE,peer)

    def sendTableFailed(self,peer):
        self.log.warning('initial swap routing table delivery to %s failed',peer)
        setValue(self,'log','initial swap routing table delivery failed')
        self.initiator=False
        self.duringSwap=False
        return

    def sendLocks(self):
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
            AskLockMessage.send(self.stream.id,[pnode],p,self.controlPipe,err_func=self.lockFailed,suc_func=self.lockSent)
        if not availableNeighs:
            self.log.debug('there are no locks to send')
            self.checkLockFinished()

    def lockFailed(self,peer):
        peer.participateSwap=False
        peer.partnerParticipateSwap=False
        self.checkLockFinished()

    def lockSent(self,peer):
        peer.checkResponse=reactor.callLater(3,self.checkStatus,LOCK_SENT,peer)

    ###REICEVED LOCK ANSWER
    def recAnsLock(self,peer,lock):
        peer.checkResponse.cancel()
        if not peer.participateSwap:
            #raise ValueError('got an unexpected lock response from %s',peer)
            self.log.error('got an unexpected lock response from  %s',peer)
            print 'got an unexpected lock response from ',peer
            setValue(self,'log','got an unexpected lock response')
            #reactor.stop()
        self.log.debug('the lock answer from %s was %s',peer,lock)
        if not lock:
            peer.participateSwap=False
            peer.partnerParticipateSwap=False

        peer.waitLock=False
        self.checkLockFinished()


    def checkLockFinished(self):
        finished=True
        for p in self.partnerTable:
            if p.participateSwap and p.waitLock:
                finished=False
                break

        if finished:
            if self.initiator:
                if self.gotPartnerUpdatedTable:
                    self.performSwap()
            else:
                self.sendUpdatedSwapTable()

    ###RECEIVED UPDATED SWAP TABLE
    def recUpdatedSwapTable(self,peer,table):
          self.log.debug('got the updated swap table from passive %s',peer)
          self.gotPartnerUpdatedTable=True
          peer.checkResponse.cancel()
          self.checkLockFinished()

    ###PERFORM SWAP
    def performSwap(self):
        self.passiveInitPeer.participateSwap=False
        partnerSet=[p for p in self.getNeighbours() if p!=self.passiveInitPeer]

        initialHoodEnergy=self.getCustomEnergy(partnerSet)+self.getCustomEnergy(self.partnerTable)

        availablePeers=[p for p in partnerSet+self.partnerTable if p.participateSwap or p.partnerParticipateSwap]
        #tempav=[p for p in partnerSet+self.partnerTable if p.participateSwap or p.partnerParticipateSwap]
        #if len(availablePeers)!=len(tempav):
        #    print availablePeers
        #    print tempav
         #   reactor.stop()

        for p in availablePeers:
            p.participateSwap=True

        initActiveLength=len(partnerSet)
        initPassiveLenght=len(self.partnerTable)
        initLength=initActiveLength+initPassiveLenght

        finalPassiveSet=int(initLength)/2
        finalActiveSet=initLength-finalPassiveSet



        activeUnavailablePeers=[p for p in partnerSet if not p.partnerParticipateSwap]
        passiveUnavailablePeers=[p for p in self.partnerTable if  not p.participateSwap]

        swapActiveLenght=finalActiveSet-len(activeUnavailablePeers)
        swapPassiveLenght=finalPassiveSet-len(passiveUnavailablePeers)
        swapLenght=swapActiveLenght+swapPassiveLenght

        if finalPassiveSet!=finalActiveSet:
            swapPassiveLenght+=1

        if swapActiveLenght<=0 or swapPassiveLenght<=0:
            #swap finished
            self.newTable=self.getNeighbours()
            self.newPartnerTable=self.partnerTable
            self.log.warning("current neughs %s",self.newTable[:])
            self.log.warning('%s',self.getNeighbours())
            self.log.warning('partner table %s',self.partnerTable[:])
            self.sendFinalTable()
            return

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
                #raise ValueError("can't perform swap with no rtt for %s",p)
                #reactor.stop()
                pass
            temp[p]=count
            G.add_edge(-3,count,capacity=1,weight=int(1000*rtt))
            G.add_edge(-4,count,capacity=1,weigth=int(1000*p.swapRtt))
            G.add_edge(count,-2,capacity=1)
            count +=1

        #flowDict=nx.min_cost_flow(G)

        try:
            flowDict=nx.min_cost_flow(G)
        except:
            for p in availablePeers:
                rtt=0
                if len(p.lastRtt):
                    rtt=sum(p.lastRtt)/len(p.lastRtt)
                print p,rtt,p.swapRtt
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print 'could not execute swap'
            self.log.error("could not execute swap")
            setValue(self,'log','could not execute swap')
            self.newTable=self.getNeighbours()
            self.newPartnerTable=self.partnerTable
            self.log.warning("current neughs %s",self.newTable[:])
            self.log.warning('%s',self.getNeighbours())
            self.log.warning('partner table %s',self.partnerTable[:])
            self.sendFinalTable()
            return

        print flowDict
        #if flowDict['src']['active']!=swapActiveLenght or flowDict['src']['passive']!=swapPassiveLenght:
        #    raise ValueError('problem in perform swap')

        newActiveTable=[p for p in availablePeers if flowDict[-3][temp[p]]==1]
        newPassiveTable=[p for p in availablePeers if flowDict[-4][temp[p]]==1]

        if len(newActiveTable)+len(newPassiveTable)!=len(availablePeers):
            #raise ValueError('problem in perform swap')
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print 'problem in perform swap'
            setValue(self,'log', 'problem in perform swap')
            print newActiveTable
            print newPassiveTable
            print availablePeers
            #reactor.stop()

        self.log.warning("current neughs %s",self.getNeighbours())
        self.log.warning('partner table %s',self.partnerTable)
        self.log.warning('unavailable %s',activeUnavailablePeers)
        self.log.warning('new %s',newActiveTable)
        self.log.warning('new passive %s',newPassiveTable)
        self.newTable=newActiveTable+activeUnavailablePeers+[self.passiveInitPeer]
        self.log.warning('passive init %s',self.passiveInitPeer)
        self.log.warning('new final %s',self.newTable)
        self.newPartnerTable=newPassiveTable+passiveUnavailablePeers

        finalHoodEnergy=self.getCustomEnergy(newActiveTable+activeUnavailablePeers)+self.getCustomEnergy(self.newPartnerTable)

        if finalHoodEnergy>initialHoodEnergy and len(self.neighbours)==len(self.newTable):
            self.log.error('major problem in swap')
            self.log.error('initial hood energy %s',initialHoodEnergy)
            self.log.error('final hood energy %s',finalHoodEnergy)
            print('initial hood energy %s',initialHoodEnergy)
            print('final hood energy %s',finalHoodEnergy)
            sys.stderr.write('problemmmmmmmmmmmmmmmmmmmm in %s\n'%self.root.netChecker.localIp)
            sys.stderr.write('%s %s\n'%(initialHoodEnergy,finalHoodEnergy))
        else:
            self.log.debug('initial hood energy %s',initialHoodEnergy)
            self.log.debug('final hood energy %s',finalHoodEnergy)

        self.sendFinalTable()

    ###SENDING FINAL TABLE TO PASSIVE
    def sendFinalTable(self):
        self.log.debug('sending final swap table to %s',self.passiveInitPeer)
        FinalSwapPeerListMessage.send(self.stream.id,self.newPartnerTable,self.passiveInitPeer,self.controlPipe,suc_func=self.finalSwapTableReceived,err_func=self.finalSwapTableFailed)
        self.partnerPeer=self.passiveInitPeer

    def finalSwapTableReceived(self,peer):
        self.updateSatelites()

    def finalSwapTableFailed(self,peer):
        self.log.warning('failed to sent final swap table to %s',self.passiveInitPeer)
        setValue(self,'log','failed to sent final swap table')
        ###clean satelites


    def updateSatelites(self):
        available=[p for p in self.newTable if p.participateSwap]
        self.log.warning('in update satelites')
        self.log.warning('new table:%s',self.newTable[:])
        self.log.warning('available:%s',available[:])
        if not available:
            self.finishSwap()
            return

        self.checkDuplicates()
        if len(self.newTable)!=len(set(self.newTable)):
            print 'duplicates in update satelites'
            setValue(self,'log','duplicates in update satelites')
            print self.newTable
            #reactor.stop()

        inpeer,port=self.root.checkNatPeer()
        bw=int(self.trafficPipe.callSimple('getBW')/1024)

        for p in available:
            if p in self.getNeighbours():
                p.swapAction=CONTINUE
                inform=None
            elif p in self.duringSwapNeighbours:
                p.swapAction=DUMMY_SUBSTITUTE
                inform=None
            else:
                inform={}
                inform['streamid']=self.stream.id
                inform['port']=port
                inform['bw']=bw
                inform['peer']=inpeer
                p.swapAction=SUBSTITUTE
            SateliteMessage.send(self.stream.id,p.swapAction,self.partnerPeer,inform,p,self.controlPipe,err_func=self.satUpdateFailed,suc_func=self.satUpdateSuccess)
            self.log.debug('sending update satelite to %s',p)
            print 'sending update satelite to ',p,' with action ',p.swapAction

    def mergeTempTable(self):
        newNeighs=[p for p in self.duringSwapNeighbours if p not in self.newTable]
        self.newTable=self.newTable+newNeighs
        self.duringSwapNeighbours=[]

    def satUpdateFailed(self,peer):
        self.log.warning('failed to update satelite %s',peer)
        self.log.info('removing %s from swap table',peer)
        setValue(self,'log','failed to update satelite')
        self.newTable.remove(peer)
        self.checkFinishSwap()

    def satUpdateSuccess(self,peer):
        peer.participateSwap=False
        self.checkFinishSwap()

    def checkFinishSwap(self):
        finish=True
        for p in self.newTable:
            if p.participateSwap:
                finish=False
                break
        if finish:
            self.finishSwap()

    def finishSwap(self):
        self.mergeTempTable()
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
        if self.shouldStop:
            self._stop()

    ###PASSIVE INITIATOR##############################

    ###RECEIVED ASK SWAP
    def recAskSwap(self,peer):
        self.log.debug('received ask swap from %s',peer)
        print 'received ask swap from ',peer
        if peer not in self.getNeighbours():
            self.log.error('he is not my neighbor so rejecting the swap') ####need to chnage and take action
            RejectSwapMessage.send(self.stream.id,peer,self.controlPipe)
            return
        if self.satelite or self.initiator or self.passiveInitiator or self.shouldStop:
            RejectSwapMessage.send(self.stream.id,peer,self.controlPipe)
            self.log.debug('and rejected it %d,%d,%d',self.satelite,self.initiator,self.passiveInitiator)
        else:
            counter(self,'swapInitiators')
            self.log.debug('and accepted it')

            self.tempSwaps+=1
            self.tempLastSwap=time()

            self.passiveInitiator=True
            self.initPeer=peer
            self.duringSwap=True
            neighs=[n for n in self.getNeighbours()]
            neighs.remove(peer)
            AcceptSwapMessage.send(self.stream.id,neighs,peer,self.controlPipe,suc_func=self.acceptReceived,err_func=self.acceptFailed)

    def acceptReceived(self,peer):
        peer.checkResponse= reactor.callLater(3,self.checkStatus,ACCEPT_SWAP,peer)

    def acceptFailed(self,peer):
        self.passiveInitiator=False
        self.duringSwap=False

    ###RECEIVED INITIAL SWAP ROUTING TABLE
    def recInitSwapTable(self,peer,peerlist):
        self.log.debug('received initial swap routing table from %s',peer)
        if peer!=self.initPeer:
            #raise ValueError('problem in receive accept swap. Accepting peer is not the passive initiator')
            print 'problem in receive accept swap. Accepting peer is not the passive initiator'
            setValue(self,'log','problem in receive accept swap. Accepting peer is not the passive initiator')
            #reactor.stop()

        peer.checkResponse.cancel()
        self.partnerTable=peerlist
        for p in peerlist:  ###should check if this is needed!!!!!!!!!!!!!!!!!!
            p.learnedFrom=peer
        self.sendLocks()

    ###SEND UPDATE SWAP TABLE
    def sendUpdatedSwapTable(self):
        self.log.debug('sending updated passive table to active initiator %s',self.initPeer)
        self.log.debug('%s',self.partnerTable[:])
        SwapPeerListMessage.send(self.stream.id, self.partnerTable, self.initPeer, self.controlPipe,err_func=self.sendUpdatedTableFailed,suc_func=self.sendUpdatedTableSuccess)

    def sendUpdatedTableFailed(self,peer):
        self.duringSwap=False
        self.passiveInitiator=False
        self.log.warning('send updated table to %s failed',peer)
        setValue(self,'log','send updated table to %s failed')
        ###should free satelites

    def sendUpdatedTableSuccess(self,peer):
        peer.checkResponse=reactor.callLater(5,self.checkStatus,SEND_UPDATE,peer)

    ###RECEIVED FINAL SWAP TABLE
    def recFinalSwapTable(self,peer,table):
        peer.checkResponse.cancel()
        self.log.debug('received final swap table from %s',self.initPeer)
        self.log.info('%s',table)
        self.newTable=table
        self.initPeer.partnerParticipateSwap=False
        self.newTable.append(self.initPeer)
        self.partnerPeer=self.initPeer
        for p in self.newTable:
            p.participateSwap=p.partnerParticipateSwap
        self.updateSatelites()


    ###SATELITES ########################################

    def recAskLock(self,peer,partner):
        self.log.debug('received ask lock from %s',peer)
        print 'received ans lock from ',peer
        if self.initiator or self.passiveInitiator or self.shouldStop:
            AnswerLockMessage.send(self.stream.id,False,peer,self.controlPipe)
            self.log.debug('and rejected it')
            print 'and rejected it'
        else:
            peer.lockPartner=partner
            counter(self,'swapSatelites')
            self.satelite+=1
            self.tempSatelites+=1
            self.tempLastSatelite=time()
            AnswerLockMessage.send(self.stream.id,True,peer,self.controlPipe,err_func=self.ansLockFailed,suc_func=self.ansLockSent)
            self.log.debug('and accepted it')
            print 'and accepted it'

    def ansLockFailed(self,peer):
        self.satelite -=1
        self.log.warning('failed to deliver possitive lock answer to %s',peer)
        print 'failed to deliver possitive lock answer to ',peer
        setValue(self,'log','failed to deliver possitive lock answer')

    def ansLockSent(self,peer):
        peer.checkResponse=reactor.callLater(10,self.checkStatus, WAIT_SWAP,peer)

    def recUpdateSatelite(self,peer,action,partner):
        self.log.debug('received update satelite from %s with partner %s',peer,partner)
        print 'received update satelite from ',peer,' with partner ',partner,' and action ',action
        if action==CONTINUE:
            self.log.debug('with action continue')
            if peer not in self.getNeighbours():
                #raise ValueError('got continue satelite from %s while he is not my neighbour',peer)
                self.log.error('got continue satelite from %s while he is not my neighbour',peer)
                print 'got continue satelite from %s while he is not my neighbour'
                setValue(self,'log','got continue satelite  while he is not my neighbour')
                #reactor.stop()
                #return
            else:
                if partner.lockPartner==peer:
                    try:
                        partner.checkResponse.cancel()
                        self.satelite -=1
                    except:
                        self.log.error('in except: got continue satatelite from wrong peer %s %s',peer,partner)
                        setValue(self,'log','in except: got continue satatelite from wrong peer')
                else:
                    self.log.error('got continue satatelite from wrong pair of peers %s %s',peer,partner)
                    setValue(self,'log','got continue satatelite from wrong pair of peers')
        elif action==DUMMY_SUBSTITUTE:
            self.log.debug('with action dummy substitute with %s',partner)
            if partner not in self.getNeighbours():
                #raise ValueError('got substitute satelite from %s while %s is not my neighbour',peer,partner)
                self.log.error( 'got dummy substitute satelite from %s while %s is not my neighbour',peer,partner)
                print 'got dummy substitute satelite from s while s is not my neighbour'
                #reactor.stop()
                setValue(self,'log','got dummy substitute satelite from s while s is not my neighbour')
                #return
            else:
                self.neighbours.remove(partner)
            if peer in self.getNeighbours():
                if peer.lockPartner==partner:
                    try:
                        peer.checkResponse.cancel()
                        self.satelite -=1
                    except:
                         self.log.error('in except: got dummy substitue from wrong pair of peers %s %s',peer,partner)
                         setValue(self,'log','in except: got dummy substitue from wrong pair of peers ')
                else:
                    self.log.error('got dummy substitue from wrong pair of peers %s %s',peer,partner)
                    setValue(self,'log','got dummy substitue from wrong pair of peers ')
            else:
                self.log.warning('problem in dummy recUpadate table %s is not already a neighbour %s',peer,partner)
                print 'problem in dummy recUpadate table s not is already a neighbour'
                setValue(self,'log', 'problem in dummy recUpadate table s not is already a neighbour')
                #reactor.stop()
                #return
        else:
            self.log.debug('with action substitute with %s',partner)
            if partner not in self.getNeighbours():
                self.log.error('got substitute satelite from %s while %s is not my neighbour',peer,partner)
                print 'got substitute satelite from s while s is not my neighbour'
                setValue(self,'log','got substitute satelite from s while s is not my neighbour')
                #reactor.stop()
                #return
            else:
                self.neighbours.remove(partner)
            if peer not in self.getNeighbours():
                if peer.lockPartner==partner:
                    self.neighbours.append(peer)
                    try:
                        peer.checkResponse.cancel()
                        self.satelite -=1
                    except:
                        self.log.error('in except: got substitute from wrong pair of peers %s %s',peer,partner)
                        setValue(self,'log','in exept: got  substitute from wrong pair of peers')
                else:
                    self.log.error('got substitute from wrong pair of peers %s %s',peer,partner)
                    setValue(self,'log','got  substitute from wrong pair of peers')
            else:
                self.log.warning('problem in recUpadate table %s is already a neighbour %s',peer,partner)
                print 'problem in recUpadate table s is already a neighbour'
                setValue(self,'log','problem in recUpadate table s is already a neighbour')
                #reactor.stop()
                #return
        self.log.info('satelite %d',self.satelite)
        self.log.info('table %s',self.getNeighbours())
        if self.satelite<0:
            self.log.error('negative value of satelite')
            print 'negative value of satelite'
            setValue(self,'log', 'negative value of satelite')
            self.satelite=0
            #reactor.stop()
        if self.initiator or self.passiveInitiator or self.duringSwap:
            self.log.error('got update satelite while in swap')
            setValue(self,'log','got update satelite while in swap')
            print 'got update satelite while in swap'
            print self.initiator,self.passiveInitiator, self.duringSwap
            print peer,partner,action
            #reactor.stop()
        if self.shouldStop:
            self._stop()

    def checkStatus(self,status,peer=None):
        setValue(self,'log','in checkstatus')
        if status==ASK_SWAP:
            self.initiator=False
            self.log.warning('never got an answer for ask swap from %s',peer)
            setValue(self,'log','never got an answer for ask swap')
        elif status==ACCEPT_SWAP:
            self.duringSwap=False
            self.passiveInitiator=False
            self.log.warning('never got an answer for accept swap from %s',peer)
            setValue(self,'log','never got an answer for accept swap')
        elif status==SEND_INIT_TABLE:
            self.log.warning('never got an answer for send init table from %s',peer)
            self.initiator=False
            self.duringSwap=False
            setValue(self,'log','never got an answer for send init table ')
            ###should clean satelites
        elif status==LOCK_SENT:
            peer.participateSwap=False
            peer.partnerParticipateSwap=False
            self.checkLockFinished()
            self.log.warning('never got an answer for ask lock from %s',peer)
            setValue(self,'log','never got an answer for ask lock')
        elif status==WAIT_SWAP:
            self.satelite -=1
            self.log.warning('never got an answer as a satelite from %s',peer)
            setValue(self,'log','never got an answer as a satelite')
        elif status==SEND_UPDATE:
            self.duringSwap=False
            self.passiveInitiator=False
            self.log.warning('never got an answer for send updated table from %s',peer)
            setValue(self,'log','never got an answer for send updated table')
            ###should free satelites

    def getEnergy(self):
        en=0
        for p in self.neighbours:
            if len(p.lastRtt):
                en +=sum(p.lastRtt)/len(p.lastRtt)
        if len(self.neighbours):
            en=en/len(self.neighbours)
        return en

    def getCustomEnergy(self,table):
        en=0
        for p in table:
            if len(p.lastRtt):
                en +=sum(p.lastRtt)/len(p.lastRtt)
        if len(table):
            en=en/len(table)
        return en

    def returnNeighs(self,peer):
        ReturnNeighsMessage.send(self.stream.id,self.neighbours,peer,self.controlPipe)

    def findNewNeighbor(self):
        neighs=[p for p in self.neighbours if not p.askedReplace]
        if len(neighs):
            askNeigh=choice(neighs)
            SuggestNewPeerMessage.send(self.stream.id,self.getNeighbours(),askNeigh,self.controlPipe,err_func=self.sendFindNewFailed)
        else:
            self.log.debug("there isn't an appropiate neighbour for asking for a new peer\n Contacting Server")
            print "there isn't an appropiate neighbour for asking for a new peer\n Contacting Server"
            SuggestNewPeerMessage.send(self.stream.id,self.getNeighbours(),Peer(self.stream.server[0],self.stream.server[1]),self.controlPipe)
            pass

    def sendFindNewFailed(self,peer):
        self.log.warning('find new neighbor message to %s failed',peer)
        setValue(self,'log','find new neighbor message failed')
        peer.askedReplace=True
        self.findNewNeighbor()

    def suggestNewPeer(self,peer,neighs):
        avNeighs=[p for p in self.neighbours if p!=peer and p not in neighs]
        SuggestMessage.send(self.stream.id,avNeighs,peer,self.controlPipe)

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
        self.sendAddNeighbour(newPeer,peer)




    def checkDuplicates(self):
        neighs=self.getNeighbours()
        if len(neighs)!=len(set(neighs)):
            setValue(self,'log','duplicate in table after swap')
            print 'DUPLICATESSSSSSSSSSSSSSSSSSSSSS'
            print neighs
            #reactor.stop()

    def collectStats(self):
        setValue(self,'energy',1000*self.getEnergy())
        setValue(self,'neighbors',len(self.getNeighbours()))

    def getVizirStats(self):
        ret=(self.tempSwaps,time()-self.tempLastSwap,self.tempSatelites,time()-self.tempLastSatelite)
        self.tempSwaps=0
        self.tempSatelites=0
        return ret

    def toggleSwap(self,stop):
        if stop:
            if self.loopingCall.running:
                self.loopingCall.stop()
        else:
            if not self.loopingCall.running:
                reactor.callLater(uniform(0.1,0.9),self.loopingCall.start,self.stream.overlay['swapFreq'])

    def sendPing(self):
        try:
            running=self.scheduler.running
        except:
            return
        if not running:
            for p in self.getNeighbours():
                PingSwapMessage.send(p,self.controlPipe)

