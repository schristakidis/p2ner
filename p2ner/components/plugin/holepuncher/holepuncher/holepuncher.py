from p2ner.core.namespace import Namespace, initNS
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

import p2ner.util.utilities as util
from messages.messages import PunchMessage,PunchReplyMessage,KeepAliveMessage,AskServerPunchMessage,StartPunchingMessage
from twisted.internet import reactor,task
from p2ner.core.pipeline import Pipeline
from p2ner.core.components import loadComponent
from time import time

class HolePuncher(Namespace):
    @initNS
    def __init__(self):
        self.peers=[]
        self.registerMessages()
        self.constructPipe()
        self.loopingCall = task.LoopingCall(self.sendKeepAlive)
        self.loopingCall.start(30)
        self.checkPeers={}
        self.mcount=0

    def registerMessages(self):
        self.messages = []
        self.messages.append(PunchMessage())
        self.messages.append(PunchReplyMessage())
        self.messages.append(KeepAliveMessage())
        self.messages.append(AskServerPunchMessage())
        self.messages.append(StartPunchingMessage())


    def constructPipe(self):
        self.holePipe=self.trafficPipe

    def check(self,msg,content,peer,d,pipe):
        if not peer:
            return
        #print 'checkinggggggg ',peer
        toCheck=[]
        if not isinstance(peer, (list, tuple)):
            peer=[peer]
        for p in peer:
            if not self.netChecker.hpunching and not p.hpunch:
                p.conOk=True
            elif p.conOk:
                p.lastSend=time()
            elif p.conProb:
                print "can't connect to peer ",p," as determined from previous try"
            elif p.hpunch or self.netChecker.hpunching and p.dataPort:
                pr=[i for i in peer if i!=p]
                if self.checkPeers.has_key(p):
                    self.checkPeers[p].append({'msg':(msg,content,peer,d,pipe),'peers':pr,'id':self.mcount})
                else:
                    self.checkPeers[p]=[{'msg':(msg,content,peer,d,pipe),'peers':pr,'id':self.mcount}]
                self.mcount+=1
                toCheck.append(p)

        #print 'to check ',toCheck
        if not toCheck:
            if len(peer)==1:
                peer=peer[0]
            pipe._send(msg,content,peer,d)
        else:
            for p in toCheck:
                reactor.callLater(0.1,self.startPunching,p)


    def sendKeepAlive(self):
        self.peers=[p for p in self.peers if p.lastSend-time()<240]

        for p in self.peers:
            print 'sending keep allive to ',p
            KeepAliveMessage.send(p, self.controlPipe,self.keepAliveFailed)
            KeepAliveMessage.send(p, self.holePipe,self.keepAliveFailed)

        servers=[s.server for s in self.root.getAllStreams()]
        if True:#self.netChecker.hpunching:
            for p in servers:
                KeepAliveMessage.send(p, self.controlPipe,self.keepAliveFailed)

    def startPunching(self,peer):
        if peer.hpunch:
            print 'sending ask server punch message to ',peer.learnedFrom,' for ',peer
            AskServerPunchMessage.send(peer,peer.learnedFrom,self.controlPipe,self._startPunching,self.failedInterPunch,peer)
        else:
            self._startPunching(None,peer)

    def failedInterPunch(self,server,peer):
        print 'failed to start punching with ',peer,' through ',server
        self.punchingFailed(peer)

    def _startPunching(self,server,peer):
        print 'punchingggggggggggggggggggggggg',peer
        PunchMessage.send(peer,'port', self.controlPipe,self.punchingFailed)
        PunchMessage.send(peer, 'dataPort', self.holePipe,self.punchingFailed)


    def receivedReply(self,peer,port):
        if port=='port':
            peer.portOk=True
        else:
            peer.dataPortOk=True
        if peer.portOk and peer.dataPortOk:
            self.peers.append(peer)
            peer.conOk=True
            print 'okkkkkkkkkkkk ',peer
            self.sendMessage(peer)



    def sendMessage(self,peer):
        clean=[]
        #print 'should send message'
        if not peer in self.checkPeers.keys():
            #print 'returning'
            return
        for m in self.checkPeers[peer]:
            send=True
            for p in m['peers']:
                if not p.conOk:
                    send=False
                    break
            msg=m['msg']
            #print msg
            if send:
                print 'sending'
                peer=msg[2]
                if len(peer)==1:
                    peer=peer[0]
                print peer
                msg[-1]._send(msg[0],msg[1],peer,msg[3])
                clean.append(m)

        if clean:
            self.cleanCheckPeers(peer,clean)

    def cleanCheckPeers(self,peer,clean):
        self.checkPeers[peer]=[m for m in self.checkPeers[peer] if m not in clean]
        if not self.checkPeers[peer]:
            self.checkPeers.pop(peer)

        for m in clean:
            id=m['id']
            for p in m['peers']:
                self.checkPeers[p]=[i for i in self.checkPeers[p] if i['id']!=id]
                if not self.checkPeers[p]:
                    self.checkPeers.pop(p)




    def punchingFailed(self,peer):
        print "hole punching failed for ",peer
        self.log.error("hole punching failed for %s",peer)
        peer.conProb=True

        try:
            actions=self.checkPeers.pop(peer)
        except:
            return

        for m in actions:
            id=m['id']
            peers=[p for p in m['peers'] if p!=peer]
            for p in peers:
                for m1 in self.checkPeers[p]:
                    m1['peers'].remove[peer]

            send=False
            if peers:
                send=True

            for p in peers:
                if not p.sendOk:
                    send=False
                    break

            if send:
                self.sendIdMessage(m)


    def sendIdMessage(self,m):
        id=m['id']
        msg=m['msg']
        peer=msg[2]
        if len(peer)==1:
            peer=peer[0]
        msg[-1]._send(msg[0],msg[1],peer,msg[3])
        clean=[]
        for p in self.checkPeers.keys():
            self.checkPeers[p]=[m1 for m1 in self.checkPeers[p] if m1['id']==id]
            if not self.checkPeers[p]:
                clean.append(p)

        for p in clean:
            self.checkPeers.pop(p)


    def punchingRecipientFailed(self,peer):
        peer.conProb=True
        print "hole punching in recipient failed for ",peer
        self.log.error("hole punching in recipient failed for %s",peer)

    def keepAliveFailed(self,peer):
        print "keep alive failed for ",peer
        self.log.error("keep alive failed for %s",peer)
