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
    type='swapsidmessage'
    code=MSG.ASK_SWAP
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recAskSwap(peer,message.swapid)

    @classmethod
    def send(cls,sid,swapid,peer,out,err_func=None,suc_func=None,args=None):
        return out.send(cls,Container(streamid=sid,swapid=swapid),peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=args)

class RejectSwapMessage(ControlMessage):
    type='swapsidmessage'
    code=MSG.REJECT_SWAP
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recRejectSwap(peer,message.swapid)

    @classmethod
    def send(cls,sid,swapid,peer,out):
        return out.send(cls,Container(streamid=sid,swapid=swapid),peer).addErrback(trap_sent)

class AcceptSwapMessage(ControlMessage):
    type='swappeerlistmessage'
    code=MSG.ACCEPT_SWAP
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recAcceptSwap(peer,message.peer,message.swapid)

    @classmethod
    def send(cls, sid, swapid,peerlist, peer, out,suc_func=None,err_func=None,args=None):
        return out.send(cls, Container(streamid=sid,swapid=swapid, peer=peerlist), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class InitSwapTableMessage(AcceptSwapMessage):
    type='swappeerlistmessage'
    code=MSG.INIT_SWAP_TABLE
    ack=True

    def action(self,message,peer):
        self['overlay'].recInitSwapTable(peer,message.peer,message.swapid)

class AskLockMessage(ControlMessage):
    type='speerlistmessage'
    code=MSG.ASK_LOCK
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recAskLock(peer,message.peer[0],message.swapid)

    @classmethod
    def send(cls, sid,swapid, peerlist, peer, out,suc_func=None,err_func=None,args=None):
        return out.send(cls, Container(streamid=sid, swapid=swapid, peer=peerlist), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class AnswerLockMessage(ControlMessage):
    type='lockmessage'
    code=MSG.ANS_LOCK
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recAnsLock(peer,message.lock,message.swapid)

    @classmethod
    def send(cls, sid,swapid, lock, peer, out,suc_func=None,err_func=None):
        return out.send(cls, Container(streamid=sid,swapid=swapid, lock=lock), peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class SwapPeerListMessage(ControlMessage):
    type = "swappeerlistmessage"
    code = MSG.SEND_UPDATED_SWAP_TABLE
    ack = True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recUpdatedSwapTable(peer,message.peer,message.swapid)

    @classmethod
    def send(cls, sid,swapid, peerlist, peer, out,err_func=None,suc_func=None):
        msg = Container(streamid = sid,swapid=swapid, peer = peerlist)
        return out.send(cls, msg, peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class FinalSwapPeerListMessage(SwapPeerListMessage):
    type = "swappeerlistmessage"
    code = MSG.SEND_FINAL_SWAP_TABLE
    ack = True


    def action(self,message,peer):
        self['overlay'].recFinalSwapTable(peer,message.peer,message.swapid)

class SateliteMessage(ControlMessage):
    type='satelitemessage'
    code=MSG.UPDATE_SATELITE
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
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
        self['overlay'].recUpdateSatelite(peer,action,p,swapid)

    @classmethod
    def send(cls, sid, swapid, action, partner,inform, peer, out,err_func=None,suc_func=None):
        if inform:
            m=Container(streamid = sid,swapid=swapid,port=inform['port'],bw=inform['bw'],peer=inform['peer'])
        else:
            m=None
        msg = Container(streamid = sid,swapid=swapid, action=action,peer = partner,overlaymessage=m)
        return out.send(cls, msg, peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=swapid)

class CleanSateliteMessage(SateliteMessage):
    type='satelitemessage'
    code=MSG.CLEAN_SATELITE
    ack=True

    def notify(self,peer,action,p,swapid):
        self['overlay'].recUpdateSatelite(peer,action,p,swapid,ack=False)

class AckUpdateMessage(ControlMessage):
    type='swapsidmessage'
    code=MSG.ACK_UPDATE
    ack=True

    def trigger(self,message):
        if self.stream.id!=message.streamid:
            return False
        return True

    def action(self,message,peer):
        self['overlay'].recAckUpdate(peer,message.swapid)

    @classmethod
    def send(cls,sid,swapid,peer,out,err_func=None,suc_func=None,args=None):
        return out.send(cls,Container(streamid=sid,swapid=swapid),peer).addErrback(probe_all,err_func=err_func,suc_func=suc_func,args=args)

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
