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


from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from construct import *

class PublishStreamMessage(ControlMessage):
    type = "streammessage"
    code = MSG.PUBLISH_STREAM
    ack = True
    
    def trigger(self, message):
        #print "TRIGGER", message
        if message.stream.id != 0:
            return False
        return True

    def action(self, message, peer):
        stream = message.stream
        #print "RECEIVED STREAM:", stream
        producer = peer
        self.log.debug('received publish stream message from %s',peer)
        stream.id = self.root.generateStreamId(producer,stream.getServer())
        self.root.newStream(producer, stream)
        

    @classmethod
    def send(cls, stream, peer, out):
        cls.log.debug('sending publish stream message to %s',peer)
        return out.send(cls, Container(stream=stream), peer).addErrback(trap_sent)
