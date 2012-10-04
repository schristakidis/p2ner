from p2ner.base.ControlMessage import ControlMessage,trap_sent
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

class ChatterMessage(ControlMessage):
    type = "basemessage"
    code = MSG.CHATTER_MSG
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        self.chatServer.newChatter(message.message['id'],message.message['username'],message.message['new'],peer)
    
    @classmethod
    def send(cls,id,username,new, peer, out):
        d=out.send(cls, Container(message={'id':id, 'username':username,'new':new}), peer)
        d.addErrback(trap_sent)
        return d
    
class ChatMessage(ControlMessage):
    type = "basemessage"
    code = MSG.CHAT_MSG
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        self.chatServer.newMessage(message.message['id'],message.message['message'],peer)
        
    @classmethod
    def send(cls,id,username,message, peer, out):
        d=out.send(cls, Container(message={'id':id, 'peer':username,'message':message}), peer)
        d.addErrback(trap_sent)
        return d