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
from messages.messages import PeerListMessage,PeerRemoveMessage,PeerRemovePMessage,PunchMessage,PunchReplyMessage,KeepAliveMessage,PeerListPMessage,SubscribeMessage,StreamIdMessage
from twisted.internet import reactor,task
from p2ner.core.pipeline import Pipeline
from p2ner.core.components import loadComponent

class HolePuncher(Namespace):
    @initNS
    def __init__(self):
        self.peers={}
        self.servers={}
        self.registerMessages()
        self.constructPipe()
        self.loopingCall = task.LoopingCall(self.sendKeepAlive)
        self.loopingCall.start(30)
        
        
    def registerMessages(self):
        self.messages = []
        self.messages.append(PeerListMessage())
        self.messages.append(PeerListPMessage())
        self.messages.append(PeerRemoveMessage())
        self.messages.append(PeerRemovePMessage())
        self.messages.append(PunchMessage())
        self.messages.append(PunchReplyMessage())
        self.messages.append(KeepAliveMessage())
        self.messages.append(SubscribeMessage())
        self.messages.append(StreamIdMessage())
        
    def constructPipe(self):
        self.holePipe=Pipeline(_parent=self.root)
        mparser = loadComponent("pipeelement", "MessageParserElement")(_parent=self.holePipe)
        multiparser = loadComponent("pipeelement", "MultiRecipientElement")(_parent=self.holePipe)
        ackparser = loadComponent("pipeelement", "AckElement")(_parent=self.holePipe)
        hparser = loadComponent("pipeelement", "HeaderParserElement")(_parent=self.holePipe)
        whparser = loadComponent("pipeelement", "WrapperHeaderParserElement")(_parent=self.holePipe)
        
        self.holePipe.append(mparser)
        self.holePipe.append(multiparser)
        self.holePipe.append(ackparser)
        self.holePipe.append(hparser)
        self.holePipe.append(whparser)
     
    def addPeer(self,peer,id):
        if self.peers.has_key(peer):
            if id not in self.peers[peer]:
                self.peers[peer].append(id)
            else:
                print "a peer with the same id allready exists in holepuncher's peers ",peer
                #raise IndexError("a peer with the same id allready exists in holepuncher's peers")
        else:
            self.peers[peer]=[id]
            self.startPunching(peer)
            
    def addServer(self,peer,id):
        if self.servers.has_key(peer):
            if id not in self.servers[peer]:
                self.servers[peer].append(id)
            else:
                print "a server with the same id allready exists in holepuncher's peers ",peer
                #raise IndexError("a peer with the same id allready exists in holepuncher's peers")
        else:
            self.servers[peer]=[id]
            
            
    def removePeer(self,peer,id):
        if not self.root.netChecker.nat:
            return
        try:
            self.peers[peer].remove(id)
            if not self.peers[peer]:
                self.peers.pop(peer)
        except:
            raise IndexError("problem in removing peer from holepuncher")
        
    def cleanPeers(self):
        s=self.root.getAllStreams()
        ids= [x.stream.id for x in s]
        for peer,id in self.peers.items():
            self.peers[peer]=[i for i in id if i in ids]
            if not self.peers[peer]:
                self.peers.pop(peer)
        for peer,id in self.servers.items():
            self.servers[peer]=[i for i in id if i in ids]
            if not self.servers[peer]:
                self.servers.pop(peer)
            
    
    def sendKeepAlive(self):
        self.cleanPeers()
        #print 'peersssss ',self.peers.keys()
        
        #!!!!!!!!!! setting as arg the whole array instead of for produces errors while calling the callback
        for p in self.peers:
            KeepAliveMessage.send(p, self.controlPipe,self.keepAliveFailed)
            KeepAliveMessage.send(p, self.holePipe,self.keepAliveFailed)
        
        for p in self.servers:
            KeepAliveMessage.send(p, self.controlPipe,self.keepAliveFailed)
            
    def startPunching(self,peer):
        PunchMessage.send(peer,'port', self.controlPipe,self.punchingFailed)
        PunchMessage.send(peer, 'dataPort', self.holePipe,self.punchingFailed)
        
    def punchingFailed(self,peer):
        print "hole punching failed for ",peer
        self.log.error("hole punching failed for %s",peer)
    
    def punchingRecipientFailed(self,peer):
        print "hole punching in recipient failed for ",peer
        self.log.error("hole punching in recipient failed for %s",peer)
    
    def keepAliveFailed(self,peer):
        print "keep alive failed for ",peer
        self.log.error("keep alive failed for %s",peer)