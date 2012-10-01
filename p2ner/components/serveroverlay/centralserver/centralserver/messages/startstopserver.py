# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage, trap_sent
from p2ner.base.Consts import MessageCodes as MSG
from twisted.internet import reactor

class ServerStartedMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.SERVER_STARTED
    ack = True
    
    def trigger(self, message):
        return message.streamid == self.stream.id

    def action(self, message, peer):
        if self.overlay.producer is peer:
                self.overlay.stream.live=True
                #print "DISPATCHING SERVER MESSAGE TO:", self.overlay.getNeighbours()
                self.log.debug('received serverStarted message from %s',peer)
                self.log.debug('sending serverStarted message to %s',str(self.overlay.getNeighbours()))
                ServerStartedMessage.send(message, self.overlay.getNeighbours(), self.controlPipe)
                self.log.debug('sending serverStarted message to producer %s',peer)
                ServerStartedMessage.send(message, self.overlay.producer, self.controlPipe)
        

    @classmethod
    def send(cls, message, peer, out):
        return out.send(cls, message, peer).addErrback(trap_sent)

class ServerStoppedMessage(ServerStartedMessage):
    type = "sidbasemessage"
    code = MSG.SERVER_STOPPED
    ack = True
    
    def action(self, message, peer):
        if self.overlay.producer is peer:
            self.overlay.stream.live=False
            if message.message==False:
                reactor.callLater(0.5,self.root.unregisterStream,self.stream.id)
            else:
                reactor.callLater(0.5,self.overlay.stop)
            self.log.debug('received serverStopped message from %s',peer)   
            #print "DISPATCHING SERVER STOP MESSAGE TO:", self.overlay.getNeighbours()
            self.log.debug('sending serverStopped message to %s',str(self.overlay.getNeighbours()))
            ServerStoppedMessage.send(message, self.overlay.getNeighbours(), self.controlPipe)
            #ServerStartedMessage.send(message, self.overlay.producer, self.controlPipe)


class StartRemoteMessage(ControlMessage):
    type='sidmessage'
    code=MSG.START_REMOTE
    ack=True
      
    def trigger(self, message):
        return message.streamid == self.stream.id

    def action(self, message, peer):
        if not self.overlay.stream.live:
            self.overlay.stream.live=True
            #print "DISPATCHING SERVER MESSAGE TO:", self.overlay.getNeighbours()
            self.log.debug('received start remote  message from %s',peer)
            self.log.debug('sending serverStarted message to %s',str(self.overlay.getNeighbours()))
            ServerStartedMessage.send(message, self.overlay.getNeighbours(), self.controlPipe)
            self.log.debug('sending serverStarted message to producer %s',peer)
            ServerStartedMessage.send(message, self.overlay.producer, self.controlPipe)
        else:
            self.log.warning('recieved start remote message for an allready live stream')
        


if __name__ == "__main__":
    a = ServerStoppedMessage()
    print a.code
    b= ServerStartedMessage()
    print b.code
