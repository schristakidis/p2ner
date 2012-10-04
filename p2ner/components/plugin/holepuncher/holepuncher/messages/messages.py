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


from p2ner.base.ControlMessage import ControlMessage, trap_sent,probe_ack
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

class PeerListMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        if self.netChecker.nat:
            for peer in message.peer:
                self.holePuncher.addPeer(peer,message.streamid)

class PeerListPMessage(PeerListMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST_PRODUCER
    ack = True
       
class PeerRemoveMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        if self.netChecker.nat:
            for peer in message.peer:
                self.holePuncher.removePeer(peer,message.streamid)

class PeerRemovePMessage(PeerRemoveMessage):
    type = "peerlistmessage"
    code = MSG.REMOVE_NEIGHBOURS_PRODUCER
    ack = True
    

class SubscribeMessage(ControlMessage):
    type = "streammessage"
    code = MSG.STREAM
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        if self.netChecker.nat:
                self.holePuncher.addServer(peer,message.stream.id)

class StreamIdMessage(ControlMessage):
    type = "sidbasemessage"
    code = MSG.STREAM_ID
    ack = True

    def trigger(self, message):
        return True

    def action(self, message, peer):
        if self.netChecker.nat:
                self.holePuncher.addServer(peer,message.streamid)



class PunchMessage(ControlMessage):
    type = "basemessage"
    code = MSG.HOLE_PUNCH
    ack = True
    
    def trigger(self, message):
        return True
    
    def action(self, message, peer):
        print 'punch message received ',message.message,peer
        if message.message=='port':
            PunchReplyMessage.send(peer,message.message, self.controlPipe,self.holePuncher.punchingRecipientFailed)
        else:
            PunchReplyMessage.send(peer,message.message, self.holePipe,self.holePuncher.punchingRecipientFailed)
    
    @classmethod
    def send(cls, peer,msg, out,func):
        msg = Container(message=msg)
        return out.send(cls, msg, peer).addErrback(probe_ack,func)
    
class PunchReplyMessage(ControlMessage):
    type = "basemessage"
    code = MSG.PUNCH_REPLY
    ack = True
    
    def trigger(self, message):
        return True
    
    def action(self, message, peer):
        print 'punch reply message received ',message.message,peer
        return True
    
    @classmethod
    def send(cls, peer,msg, out,func):
        msg = Container(message=msg)
        return out.send(cls, msg, peer).addErrback(probe_ack,func)
    
class KeepAliveMessage(ControlMessage):
    type = "basemessage"
    code = MSG.KEEP_ALIVE
    ack = True

    def trigger(self, message):
        return True
    
    def action(self, message, peer):
        print 'keep alive message received'
        return True    
    
    @classmethod
    def send(cls, peer, out,func):
        msg = Container(message=None)
        return out.send(cls, msg, peer).addErrback(probe_ack,func)