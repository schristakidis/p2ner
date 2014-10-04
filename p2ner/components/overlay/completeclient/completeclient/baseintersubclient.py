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
from subclient import SubClient

ASK_SWAP=0
ACCEPT_SWAP=1
LOCK_SENT=2
WAIT_SWAP=3
SEND_UPDATE=4
SEND_INIT_TABLE=5

CONTINUE=0
INSERT=1
REMOVE=2

class SubOverlay(SubClient):

    def registerMessages(self):
        self.messages = []
        self.messages.append(ClientStoppedMessage())
        self.messages.append(PeerListMessage())
        self.messages.append(ConfirmNeighbourMessage())
        self.messages.append(AskLockMessage())
        self.messages.append(SateliteMessage())
        self.messages.append(PingMessage())
        self.messages.append(PingSwapMessage())
        self.messages.append(SuggestMessage())
        self.messages.append(CleanSateliteMessage())
        self.messages.append(ValidateNeighboursMessage())
        self.messages.append(ReplyValidateNeighboursMessage())


    def startSwap(self):
        return

    def checkSendAddNeighbour(self,peer,originalPeer):
        if not peer:
            reactor.callLater(2,self.askInitialNeighbours)
            return
        super(SubClient,self).checkSendAddNeighbour(peer,originalPeer)

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

        self.log.info('should find a new neighbor')
        print 'should find a new neighbor'
        for p in self.neighbours:
            p.askedReplace=False
        self.findNewNeighbor()



    def toggleSwap(self,stop):
        return

