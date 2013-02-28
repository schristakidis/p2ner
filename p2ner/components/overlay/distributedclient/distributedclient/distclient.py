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
from messages.peerlistmessage import *
from messages.peerremovemessage import ClientStoppedMessage
from twisted.internet import task,reactor
from random import choice,uniform
from messages.swapmessages import *
from time import time
import networkx as nx
from p2ner.base.Peer import Peer

ASK_SWAP=0
ACCEPT_SWAP=1
LOCK_SENT=2
WAIT_SWAP=3
SEND_UPDATE=4
SEND_INIT_TABLE=5

CONTINUE=0
SUBSTITUTE=1

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
        
    def initOverlay(self):
        self.log.info('initing overlay')
        print 'initing overlay'
        self.sanityCheck(["stream", "control", "controlPipe"])

        
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
        #self.loopingCall.start(self.stream.overlay['swapFreq'])

        
    def getNeighbours(self):
        return self.neighbours[:]
    
    def addNeighbour(self, peer):
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
            PingMessage.send(peer,self.controlPipe)
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
                    
    def isNeighbour(self, peer):
        return peer in self.neighbours
    
    def stop(self):
        self.log.info('stopping overlay')
        self.log.debug('sending clientStopped message to %s',self.server)
        try:
            self.loopingCall.stop()
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
        

    ###ACTIVE INITIATOR ##########################3
    
    ### ASK SWAP
    def startSwap(self):
        self.log.debug('starting swap')
        if self.satelite or self.initiator or self.passiveInitiator or len(self.neighbours)<=1:
            self.log.debug('no available conditions for swap')
            return
        
        self.initiator=True
        peer=choice(self.neighbours)
        self.log.warning('%s',self.getNeighbours())
        self.log.debug('sending ask swap message to %s',peer)
        AskSwapMessage.send(self.stream.id,peer,self.controlPipe,err_func=self.askFailed,suc_func=self.askReceived)
        
    def askFailed(self,peer):
        self.log.debug('ask swap to %s failed',peer)
        print 'ask swap to ',peer,'failed'
        self.initiator=False
        
    def askReceived(self,peer):
        self.passiveInitPeer=peer
        self.passiveInitPeer.checkResponse= reactor.callLater(3,self.checkStatus,ASK_SWAP,peer)
        
        
    ###RECEIVED REJECT SWAP
    def recRejectSwap(self,peer):
        if peer!=self.passiveInitPeer:
            raise ValueError('problem in receive reject swap. Rejecting peer is not the passive initiator')
        self.log.debug('swap was rejected from %s',peer)
        peer.checkResponse.cancel()
        self.initiator=False
        
    ###RECEIVED ACCEPT SWAP
    def recAcceptSwap(self,peer,peerlist):
        if peer!=self.passiveInitPeer:
            raise ValueError('problem in receive accept swap. Accepting peer is not the passive initiator')
        peer.checkResponse.cancel()
        self.log.debug('swap accepted from %s',peer)
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
        self.initiator=False
        self.duringSwap=False
        return
        
    def sendLocks(self):
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
            AskLockMessage.send(self.stream.id,p,self.controlPipe,err_func=self.lockFailed,suc_func=self.lockSent)
        if not availableNeighs:
            self.log.debug('there are no locks to send')
            self.checkLockFinished()
            
    def lockFailed(self,peer):
        p.participateSwap=False
        self.checkLockFinished()
        
    def lockSent(self,peer):
        peer.checkResponse=reactor.callLater(3,self.checkStatus,LOCK_SENT,peer)
        
    ###REICEVED LOCK ANSWER 
    def recAnsLock(self,peer,lock):
        peer.checkResponse.cancel()
        if not peer.participateSwap:
            raise ValueError('got an unexpected lock response from %s',peer)
        self.log.debug('the lock answer from %s was %s',peer,lock)
        if not lock:
            peer.participateSwap=False
        else:
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

        
        availablePeers=[p for p in partnerSet+self.partnerTable if p.participateSwap or p.partnerParticipateSwap]
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
                raise ValueError("can't perform swap with no rtt for %s",p)
            temp[p]=count
            G.add_edge(-3,count,capacity=1,weight=rtt)
            G.add_edge(-4,count,capacity=1,weigth=p.swapRtt)
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
            raiseValueError('problem in perform swap')
            
        self.log.warning("current neughs %s",self.getNeighbours())
        self.log.warning('partner table %s',self.partnerTable)
        self.log.warning('unavailable %s',activeUnavailablePeers)
        self.log.warning('new %s',newActiveTable)
        self.log.warning('new passive %s',newPassiveTable)
        self.newTable=newActiveTable+activeUnavailablePeers+[self.passiveInitPeer]
        self.log.warning('passive init %s',self.passiveInitPeer)
        self.log.warning('new final %s',self.newTable)
        self.newPartnerTable=newPassiveTable+passiveUnavailablePeers
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
        ###clean satelites
         
        
    def updateSatelites(self):
        self.mergeTempTable()
        available=[p for p in self.newTable if p.participateSwap]
        self.log.warning('in update satelites')
        self.log.warning('new table:%s',self.newTable[:])
        self.log.warning('available:%s',available[:])
        if not available:
            self.finishSwap()
            return

        for p in available:
            if p in self.getNeighbours():
                p.swapAction=CONTINUE
            else:
                p.swapAction=SUBSTITUTE
            SateliteMessage.send(self.stream.id,p.swapAction,self.partnerPeer,p,self.controlPipe,err_func=self.satUpdateFailed,suc_func=self.satUpdateSuccess)
            self.log.debug('sending update satelite to %s',p)
            
    def mergeTempTable(self):
        newNeighs=[p for p in self.duringSwapNeighbours if p not in self.newTable]
        self.newTable=self.newTable+self.duringSwapNeighbours
        self.duringSwapNeighbours=[]
        
    def satUpdateFailed(self,peer):
        self.log.warning('failed to update satelite %s',peer)
        self.log.info('removing %s from swap table',peer)
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
        
    ###PASSIVE INITIATOR##############################
    
    ###RECEIVED ASK SWAP
    def recAskSwap(self,peer):
        self.log.debug('received ask swap from %s',peer)
        print 'received ask swap from ',peer
        if self.satelite or self.initiator or self.passiveInitiator:
            RejectSwapMessage.send(self.stream.id,peer,self.controlPipe)
            self.log.debug('and rejected it')
        else:
            self.log.debug('and accepted it')
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
            raise ValueError('problem in receive accept swap. Accepting peer is not the passive initiator')
        
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
    
    def recAskLock(self,peer):
        self.log.debug('received ask lock from %s',peer)
        if self.initiator or self.passiveInitiator:
            AnswerLockMessage.send(self.stream.id,False,peer,self.controlPipe)
            self.log.debug('and rejected it')
        else:
            self.satelite+=1
            AnswerLockMessage.send(self.stream.id,True,peer,self.controlPipe,err_func=self.ansLockFailed,suc_func=self.ansLockSent)
            self.log.debug('and accepted it')
            
    def ansLockFailed(self,peer):
        self.satelite -=1
        self.log.warning('failed to deliver possitive lock answer to %s',peer)
        
    def ansLockSent(self,peer):
        peer.checkResponse=reactor.callLater(10,self.checkStatus, WAIT_SWAP,peer)
        
    def recUpdateSatelite(self,peer,action,partner):
        self.log.debug('received update satelite from %s with partner %s',peer,partner)
        if action==CONTINUE:
            self.log.debug('with action continue')
            if peer not in self.getNeighbours():
                raise ValueError('got continue satelite from %s while he is not my neighbour',peer)
            self.satelite -=1
            partner.checkResponse.cancel()
        else:
            self.log.debug('with action substitute with %s',partner)
            if partner not in self.getNeighbours():
                raise ValueError('got substitute satelite from %s while %s is not my neighbour',peer,partner)
            self.neighbours.remove(partner)
            if peer not in self.getNeighbours():
                self.neighbours.append(peer)
            else:
                self.log.warning('problem in recUpadate table %s is already a neighbour %s',peer,partner)
            self.satelite -=1
            peer.checkResponse.cancel()
        self.log.info('satelite %d',self.satelite)
        self.log.info('table %s',self.getNeighbours())
        
    def checkStatus(self,status,peer=None):
        if status==ASK_SWAP:
            self.initiator=False
            self.log.warning('never got an answer for ask swap from %s',peer)
        elif status==ACCEPT_SWAP:
            self.duringSwap=False
            self.passiveInitiator=False
            self.log.warning('never got an answer for accept swap from %s',peer)
        elif status==SEND_INIT_TABLE:
            self.log.warning('never got an answer for send init table from %s',peer)
            self.initiator=False
            self.duringSwap=False
            ###should clean satelites
        elif status==LOCK_SENT:
            peer.participateSwap=False
            self.checkLockFinished()
            self.log.warning('never got an answer for ask lock from %s',peer)
        elif status==WAIT_SWAP:
            self.satelite -=1
            self.log.warning('never got an answer as a satelite from %s',peer)
        elif status==SEND_UPDATE:
            self.duringSwap=False
            self.passiveInitiator=False
            self.log.warning('never got an answer for send updated table from %s',peer)
            ###should free satelites
        
    def getEnergy(self):
        en=0
        for p in self.neighbours:
            if len(p.lastRtt):
                en +=sum(p.lastRtt)/len(p.lastRtt)
        if len(self.neighbours):
            en=en/len(self.neighbours)
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
        newPeer.learnedFrom=peer
        self.log.debug('received available peers message from %s with %s',peer,newPeer)
        print 'receive  available peers message from ',peer,' with ',newPeer
        inpeer,port=self.root.checkNatPeer()
        bw=int(self.trafficPipe.getElement("BandwidthElement").bw/1024)
        AddNeighbourMessage.send(self.stream.id,port,bw,inpeer,p,self.addNeighbour,self.failedNeighbour,self.root.controlPipe)
        
            