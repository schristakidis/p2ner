from p2ner.base.ControlMessage import ControlMessage, probe_ack
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
from cPickle import dumps
from twisted.internet import reactor

class PingMessage(ControlMessage):
    type = "basemessage"
    code = MSG.PING
    ack = False

    def initMessage(self, server):
        self.server=server
        self.response=False
        reactor.callLater(2,self.checkResponse)
        
    def trigger(self, message):
        return True

    def action(self, message, peer):
        if peer!=self.server:
            return
        self.log.debug('received ping message from %s',peer)
        m=self.netChecker.pingListeners.index(self)
        self.netChecker.pingListeners.remove(self)
        self.response=True
        self.netChecker.pingResults(self.server,True)


    def checkResponse(self):
        if not self.response:
            m=self.netChecker.pingListeners.index(self)
            self.netChecker.pingListeners.remove(self)
            self.netChecker.pingResults(self.server,False)
            
    @classmethod
    def send(cls,  server, out):
        d = out.send(cls, Container(message=None), server)
        d.addErrback(probe_ack)
        return d
        
        
class CheckPortMessage(ControlMessage):
    type = "basemessage"
    code = MSG.CHECK_PORT
    ack = False

    def initMessage(self, server):
        self.server=server
        self.response=False
        reactor.callLater(2,self.checkResponse)
        
    def trigger(self, message):
        return True

    def action(self, message, peer):
        if peer!=self.server:
            return
        self.log.debug('received ckeck port message from %s',peer)
        ControlMessage.remove_refs(self)
        self.response=True
        self.netChecker.checkPortResults(self.server,True,message.message)


    def checkResponse(self):
        if not self.response:
            self.log.error('failed to receive ckeck port message from %s',self.server)
            ControlMessage.remove_refs(self)
            self.netChecker.checkPortResults(self.server,False)
            
    @classmethod
    def send(cls,  server, port, out):
        d = out.send(cls, Container(message=port), server)
        d.addErrback(probe_ack)
        return d
    
class GetXPortMessage(ControlMessage):
    type = "basemessage"
    code = MSG.GET_XPORT
    ack = True
    
    def initMessage(self,port):
        self.port=port
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        ControlMessage.remove_refs(self)
        self.netChecker.setXPort(message.message,self.port)
        
    @classmethod
    def send(cls, port,nat, server,out,func):
         out.send(cls, Container(message={'port':port,'nat':nat}), server).addErrback(probe_ack,func)
            
