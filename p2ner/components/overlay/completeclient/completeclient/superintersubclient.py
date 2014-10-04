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
from subclient import SubOverlay as SubClient

ASK_SWAP=0
ACCEPT_SWAP=1
LOCK_SENT=2
WAIT_SWAP=3
SEND_UPDATE=4
SEND_INIT_TABLE=5

CONTINUE=0
INSERT=1
REMOVE=2

class SuperInterOverlay(SubClient):

    def registerMessages(self):
        self.messages = []
        self.messages.append(ClientStoppedMessage())
        self.messages.append(AddNeighbourMessage())
        self.messages.append(AskSwapMessage())
        self.messages.append(RejectSwapMessage())
        self.messages.append(AcceptSwapMessage())
        self.messages.append(InitSwapTableMessage())
        self.messages.append(AnswerLockMessage())
        self.messages.append(SwapPeerListMessage())
        self.messages.append(FinalSwapPeerListMessage())
        self.messages.append(PingMessage())
        self.messages.append(PingSwapMessage())
        self.messages.append(SuggestNewPeerMessage())
        self.messages.append(AckUpdateMessage())
        self.messages.append(ValidateNeighboursMessage())
        self.messages.append(ReplyValidateNeighboursMessage())

    def askInitialNeighbours(self):
        return

    def getSuperNeighbours(self):
        return self.parent.subOverlays['super'].getNeighbours()

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


    def choosePassiveInitiatorPeer(self):
        return choice(self.getSuperNeighbours())

    def checkValidNumNeighsForSwap(self):
        return len(self.getSuperNeighbours())

    def getInitialSwapTable(self):
        return self.getNeighbours()

    def constructFinalInitiatorTable(self,table):
        return table

    def checkExecuteSwapTwice(self,initiatorTable,passiveTable):
        initActiveLength=len(initiatorTable)
        initPassiveLenght=len(passiveTable)
        initLength=initActiveLength+initPassiveLenght

        return initLength%2!=0

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

    def checkValidInitiator(self,peer):
        return peer in self.getSuperNeighbours()

    def getInitialPassiveTable(self,peer):
        neighs=self.getNeighbours()
        return neighs

    def constructFinalPassiveTable(self,table):
        return table


    def suggestNewPeer(self,peer,neighs):
        avNeighs=[p for p in self.getSuperNeighbours() if p!=peer and p not in neighs]
        SuggestMessage.send(self.stream.id,self.superOverlay,self.interOverlay,avNeighs,peer,self.controlPipe)


