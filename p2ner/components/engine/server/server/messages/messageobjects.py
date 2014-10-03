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


from construct import Container
from p2ner.base.Consts import MessageCodes as MSG
from p2ner.base.ControlMessage import trap_sent,BaseControlMessage

class StreamIdMessage(BaseControlMessage):
    type = "sidbasemessage"
    code = MSG.STREAM_ID
    ack = True

    @classmethod
    def send(cls, streamID, streamhash, peer, out):
        out.log.debug('sending streamid message to %s',peer)
        msg = Container(streamid = streamID, message = streamhash)
        return out.send(cls, msg, peer).addErrback(trap_sent)



class ContentsMessage(BaseControlMessage):
    type='mstreammessage'
    code=MSG.GET_CONTENTS
    ack=True

    @classmethod
    def send(cls,stream,peer,out):
        out.log.debug('sending contents message to %s',peer)
        return out.send(cls,Container(stream=stream),peer).addErrback(trap_sent)
