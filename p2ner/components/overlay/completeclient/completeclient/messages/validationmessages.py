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


from p2ner.base.ControlMessage import ControlMessage, trap_sent,probe_all,BaseControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

class ValidateNeighboursMessage(ControlMessage):
    type = "subsidmessage"
    code = MSG.VALIDATE_NEIGHS_SUB
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid or self.superOverlay!=message.superOverlay or self.interOverlay!=message.interOverlay:
            return False
        return True

    def action(self, message, peer):
        self.subOverlay.ansValidateNeighs(peer)

    @classmethod
    def send(cls, sid,sover,iover, peer, out):
        d=out.send(cls, Container(streamid = sid, superOVerlay=sover, interOverlay=iover), peer)
        d.addErrback(trap_sent)
        return d

class ReplyValidateNeighboursMessage(ControlMessage):
    type='sublockmessage'
    code = MSG.REPLY_VALIDATE_NEIGHS_SUB
    ack=True

    def trigger(self, message):
        if self.stream.id != message.streamid or self.superOverlay!=message.superOverlay or self.interOverlay!=message.interOverlay:
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.checkValidateNeighs(message.lock,peer)
        return

    @classmethod
    def send(cls, sid, sover, iover, ans , peer, out):
        return out.send(cls, Container(streamid=sid, superOverlay=sover, interOverlay=iover, swapid=0, lock=ans), peer).addErrback(trap_sent)
