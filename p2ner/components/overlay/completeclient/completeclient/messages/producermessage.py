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



class PeerListPMessage(ControlMessage):
    type = "peerlistmessage"
    code = MSG.SEND_IP_LIST_PRODUCER
    ack = True

    def trigger(self, message):
        if self.stream.id != message.streamid:
            return False
        return True

    def action(self, message, peer):
        self.log.debug('received peerList message from %s for %s',peer,str(message.peer))
        print 'receive peer list message for producer from ',peer,' for ',message.peer
        inpeer=self.root.getPeerObject()
        bw=min(65535,int(self.trafficPipe.callSimple('getReportedCap')))
        for p in message.peer:
            p.learnedFrom=peer
            print 'sending add producer message to ',p
            AddProducerMessage.send(self.stream.id,0,bw,inpeer,p,self.overlay.addProducer,self.overlay.failedProducer,self.root.controlPipe)





class AddProducerMessage(BaseControlMessage):
    type = "overlaymessage"
    code = MSG.ADD_PRODUCER
    ack = True


    @classmethod
    def send(cls, id,port,bw, inpeer, peer,suc_func,err_func, out):
        msg = Container(streamid=id,port=port, bw=bw,peer=inpeer)
        d=out.send(cls, msg, peer)
        d.addErrback(probe_all,suc_func=suc_func,err_func=err_func)
        return d

class PingMessage(ControlMessage):
    type='basemessage'
    code=MSG.ADDNEIGH_RTT
    ack=True

    def trigger(self,message):
        return True

    def action(self,message,peer):
        return

    @classmethod
    def send(cls,  peer, out):
        out.send(cls,Container(message=None),peer).addErrback(trap_sent)

