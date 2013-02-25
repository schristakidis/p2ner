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

class AskNeighboursMessage(BaseControlMessage):
    type='basemessage'
    code=MSG.GET_NEIGHS
    ack=True
       
    @classmethod
    def send(cls,  peer, id, out):
        out.send(cls,Container(message=id),peer).addErrback(trap_sent)
        
class GetNeighboursMessage(ControlMessage):
    type='swappeerlistmessage'
    code=MSG.RETURN_NEIGHS
    ack=True
        
    def initMessage(self,peer,func):
        self.peer=peer
        self.func=func
        
    def trigger(self,message):
        if message.streamid!=self.stream.id:
            return False
        return True
    
    def action(self,message,peer):
        if peer!=self.peer:
            return 
        self.func(peer,message.peer)