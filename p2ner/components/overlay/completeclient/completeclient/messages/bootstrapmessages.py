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


from p2ner.base.ControlMessage import ControlMessage, trap_sent,probe_ack,BaseControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container

class AskServerForStatus(BaseControlMessage):
    type = "bwmessage"
    code = MSG.ASK_OVERLAY_STATUS
    ack = True

    @classmethod
    def send(cls, sid, bw, peer,  err_func,out):
        d=out.send(cls, Container(streamid = sid, bw=bw), peer)
        d.addErrback(probe_ack,err_func)
        return d


class GetPeerStatusMessage(ControlMessage):
    type = "overlaystatusmessage"
    code = MSG.GET_OVERLAY_STATUS
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self.overlay.formSubOverlays(message.superPeer)

