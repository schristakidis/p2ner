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

class AskSwapMessage(ControlMessage):
    type='subswapsidmessage'
    code=MSG.ASK_SWAP_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerInitiatorsMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recAskSwap(peer,message.swapid)

    @classmethod
    def send(cls,sid,sOver,iOver,swapid,peer,out,err_func=None,suc_func=None,args=None):
        return out.send(cls,Container(streamid=sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid),peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=args)

class RejectSwapMessage(ControlMessage):
    type='subswapsidmessage'
    code=MSG.REJECT_SWAP_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerInitiatorsMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recRejectSwap(peer,message.swapid)

    @classmethod
    def send(cls,sid,sOver,iOver,swapid,peer,out):
        return out.send(cls,Container(streamid=sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid),peer).addErrback(trap_sent)

class AcceptSwapMessage(ControlMessage):
    type='subswappeerlistmessage'
    code=MSG.ACCEPT_SWAP_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerInitiatorsMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recAcceptSwap(peer,message.peer,message.swapid)

    @classmethod
    def send(cls, sid,sOver,iOver, swapid,peerlist, peer, out,suc_func=None,err_func=None,args=None):
        return out.send(cls, Container(streamid=sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid, peer=peerlist), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class InitSwapTableMessage(AcceptSwapMessage):
    type='subswappeerlistmessage'
    code=MSG.INIT_SWAP_TABLE_SUB
    ack=True

    def action(self,message,peer):
        self.subOverlay.recInitSwapTable(peer,message.peer,message.swapid)

class AskLockMessage(ControlMessage):
    type='subspeerlistmessage'
    code=MSG.ASK_LOCK_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recAskLock(peer,message.peer[0],message.swapid)

    @classmethod
    def send(cls, sid,sOver,iOver,swapid, peerlist, peer, out,suc_func=None,err_func=None,args=None):
        return out.send(cls, Container(streamid=sid, superOverlay=sOver, interOverlay=iOver, swapid=swapid, peer=peerlist), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class AnswerLockMessage(ControlMessage):
    type='sublockmessage'
    code=MSG.ANS_LOCK_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recAnsLock(peer,message.lock,message.swapid)

    @classmethod
    def send(cls, sid,sOver,iOver,swapid, lock, peer, out,suc_func=None,err_func=None):
        return out.send(cls, Container(streamid=sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid, lock=lock), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class SwapPeerListMessage(ControlMessage):
    type = "subswappeerlistmessage"
    code = MSG.SEND_UPDATED_SWAP_TABLE_SUB
    ack = True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerInitiatorsMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recUpdatedSwapTable(peer,message.peer,message.swapid)

    @classmethod
    def send(cls, sid,sOver,iOver,swapid, peerlist, peer, out,err_func=None,suc_func=None):
        msg = Container(streamid = sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid, peer = peerlist)
        return out.send(cls, msg, peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class FinalSwapPeerListMessage(SwapPeerListMessage):
    type = "subswappeerlistmessage"
    code = MSG.SEND_FINAL_SWAP_TABLE_SUB
    ack = True


    def action(self,message,peer):
        self.subOverlay.recFinalSwapTable(peer,message.peer,message.swapid)

class SateliteMessage(ControlMessage):
    type='subsatelitemessage'
    code=MSG.UPDATE_SATELITE_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        if message.overlaymessage:
            p=message.overlaymessage
            peer.dataPort=p.port
            peer.reportedBW=p.bw
            if p.peer:
                peer.lip=p.peer.ip
                peer.lport=p.peer.port
                peer.ldataPort=p.peer.dataPort
                peer.hpunch=p.peer.hpunch

        self.notify(peer,message.action,message.peer,message.swapid)

    def notify(self,peer,action,p,swapid):
        self.subOverlay.recUpdateSatelite(peer,action,p,swapid)

    @classmethod
    def send(cls, sid,sOver,iOver, swapid, action, partner,inform, peer, out,err_func=None,suc_func=None):
        if inform:
            m=Container(streamid = sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid,port=inform['port'],bw=inform['bw'],peer=inform['peer'])
        else:
            m=None
        msg = Container(streamid = sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid, action=action,peer = partner,overlaymessage=m)
        return out.send(cls, msg, peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class CleanSateliteMessage(SateliteMessage):
    type='subsatelitemessage'
    code=MSG.CLEAN_SATELITE_SUB
    ack=True

    def notify(self,peer,action,p,swapid):
        self.subOverlay.recUpdateSatelite(peer,action,p,swapid,ack=False)

class AckUpdateMessage(ControlMessage):
    type='subswapsidmessage'
    code=MSG.ACK_UPDATE_SUB
    ack=True

    def trigger(self,message):
        if self.stream.id != message.streamid or not self.subOverlay.checkTriggerMessage(message.superOverlay,message.interOverlay):
            return False
        return True

    def action(self,message,peer):
        self.subOverlay.recAckUpdate(peer,message.swapid)

    @classmethod
    def send(cls,sid,sOver,iOver,swapid,peer,out,err_func=None,suc_func=None,args=None):
        return out.send(cls,Container(streamid=sid,superOverlay=sOver,interOverlay=iOver,swapid=swapid),peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=args)

class PingSwapMessage(ControlMessage):
    type='basemessage'
    code=MSG.PING_SWAP
    ack=True

    def trigger(self,message):
        return True

    def action(self,message,peer):
       return

    @classmethod
    def send(cls,peer,out,err_func=None,suc_func=None):
        msg=Container(message=None)
        return out.send(cls,msg,peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func)
