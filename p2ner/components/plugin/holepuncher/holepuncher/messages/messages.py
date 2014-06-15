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

from p2ner.base.ControlMessage import ControlMessage, trap_sent,probe_ack,probe_rec,probe_all,BaseControlMessage

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container


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
    def send(cls, peer,msg, out,err_func):
        msg = Container(message=msg)
        d=out._send(cls, msg, peer).addErrback(probe_all,err_func=err_func)
        return d

class PunchReplyMessage(ControlMessage):
    type = "basemessage"
    code = MSG.PUNCH_REPLY
    ack = True

    def trigger(self, message):
        return True

    def action(self, message, peer):
        print 'punch reply message received ',message.message,peer
        self.root.holePuncher.receivedReply(peer,message.message)
        return True

    @classmethod
    def send(cls, peer,msg, out,err_func,suc_func=None):
        msg = Container(message=msg)
        return out._send(cls, msg, peer).addErrback(probe_all,suc_func,err_func)

class KeepAliveMessage(ControlMessage):
    type = "basemessage"
    code = MSG.KEEP_ALIVE
    ack = True

    def trigger(self, message):
        return True

    def action(self, message, peer):
        print 'keep alive message received from ',peer
        return True

    @classmethod
    def send(cls, peer, out,func):
        msg = Container(message=None)
        return out._send(cls, msg, peer).addErrback(probe_ack,func)

class AskServerPunchMessage(ControlMessage):
    type = "peermessage"
    code = MSG.PUNCH_SERVER
    ack = True


    def trigger(self, message):
        return True

    def action(self, message, peer):
        print 'receive message from ',peer,' to help punching with ',message.peer
        StartPunchingMessage.send(peer,message.peer,self.root.controlPipe)
        return True

    @classmethod
    def send(cls, peer , server, out,suc_func, err_func, arg):
        d=out._send(cls, Container(peer=peer), server)
        d.addErrback(probe_all,suc_func,err_func,**{'peer':arg})
        return d


class StartPunchingMessage(ControlMessage):
    type = "peermessage"
    code = MSG.START_PUNCH
    ack = True

    def trigger(self, message):
        return True

    def action(self, message, peer):
        print 'receive message from ',peer,' to start punching with ',message.peer
        self.root.holePuncher._startPunching(None,message.peer,init=False)
        return True

    @classmethod
    def send(cls, peer , server, out):
        d=out._send(cls, Container(peer=peer), server)
        d.addErrback(trap_sent)
        return d

