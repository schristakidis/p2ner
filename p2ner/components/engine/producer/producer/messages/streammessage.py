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


from p2ner.base.ControlMessage import ControlMessage, BaseControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container


class StreamMessage(BaseControlMessage):
    type = "streammessage"
    code = MSG.PUBLISH_STREAM
    ack = True

    @classmethod
    def send(cls, stream, server, out):
        return out.send(cls, Container(stream=stream), server).addErrback(trap_sent)

class StreamIdMessage(ControlMessage):
    type = "sidbasemessage"
    code = MSG.STREAM_ID
    ack = True

    def initMessage(self, stream):
        self.stream = stream
        self.hash = stream.streamHash()
        
    def trigger(self, message):
        if message.message == self.hash:
            return True
        return False

    def action(self, message, peer):
        self.root.sidListeners.remove(self)
        self.stream.id = message.streamid
        self.root.newStream(self.stream)
        
