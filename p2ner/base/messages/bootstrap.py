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


from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import BaseControlMessage, trap_sent

class ClientStartedMessage(BaseControlMessage):
    type = "basemessage"
    code = MSG.CLIENT_STARTED
    ack = True
    
    @classmethod
    def send(cls, port, server, out):
        msg = Container(message=port)
        return out.send(cls, msg, server).addErrback(trap_sent)

