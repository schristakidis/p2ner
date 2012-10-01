# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from cPickle import dumps
from twisted.internet import reactor

class StreamIdMessage(ControlMessage):
    type = "sidbasemessage"
    code = MSG.STREAM_ID
    ack = True

    def initMessage(self, stream,input=None,output=None):
        self.stream = stream
        self.hash = stream.streamHash()
        self.inMethod=input
        self.outMethod=output

        
    def trigger(self, message):
        if message.message == self.hash:
            return True
        return False

    def action(self, message, peer):
        self.log.debug('received stream id message from %s',peer)
        self.root.sidListeners.remove(self)
        self.stream.id = message.streamid
        self.root.newStream(self.stream,self.inMethod,self.outMethod)
        self.interface.returnProducedStream(self.stream)

    def checkResponse(self,peer=None):
        self.log.debug('failed to receive stream id message')
        m=self.root.sidListeners.index(self)
        self.root.sidListeners.remove(self)
        self.interface.returnProducedStream(-1)
            
            
class ContentsMessage(ControlMessage):
    type='mstreammessage'
    code=MSG.GET_CONTENTS
    ack=True
    
    def initMessage(self,server):
        self.server=server
        
    def trigger(self,message):
        return True
        
    def action(self,message,peer):
        if peer != self.server:
            return 
        self.log.debug('received contents message from %s',peer)
        self.root.checkServers.pop(self.server)
        self.interface.returnContents(message.stream,(self.server.getIP(),self.server.getPort()))
        
    def checkResponse(self,peer=None):
        self.log.debug('failed to receive contents message from %s',self.server)
        self.interface.returnContents(-1,(self.server.getIP(),self.server.getPort()))
        self.root.checkServers.pop(self.server)
        

   

        
class SubscribeMessage(ControlMessage):
    type = "streammessage"
    code = MSG.STREAM
    ack = True
    
    def initMessage(self,id,output=None):
        self.id=id
        self.output=output
        
    def trigger(self, message):
        if self.id==message.stream.id:
            return True
        return False

    def action(self, message, peer):
        self.log.debug('received subscribe stream message from %s',peer)
        self.response=True
        self.root.streamListeners.remove(self)
        self.root.newSubStream(message.stream,self.id,self.output)
        
    def checkResponse(self,peer=None):
        self.log.debug('failed to receive subscribe stream message for id %s',self.id)
        self.root.streamListeners.remove(self)
        self.root.newSubStream(-1,self.id)
    


        

    
    
