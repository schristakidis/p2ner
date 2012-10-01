# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG

class ClientStartedMessage(ControlMessage):
    type = "registermessage"
    code = MSG.CLIENT_STARTED
    ack = True
    
    def trigger(self, message):
        return True

    def action(self, message, peer):
        peer.dataPort=message.port
        peer.reportedBW=message.bw
        if message.peer:
            peer.lip=message.peer.ip
            peer.lport=message.peer.port
            peer.ldataPort=message.peer.dataPort
        
        print 'received client started message from ',peer,' bw:',message.bw
     
        self.log.debug('received client started message from %s',peer)
        if peer not in self.knownPeers:
            self.knownPeers.append(peer)        
            self.log.debug('appending %s to known peers',peer)



