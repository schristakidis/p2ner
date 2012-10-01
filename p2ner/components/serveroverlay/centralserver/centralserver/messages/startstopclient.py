# -*- coding: utf-8 -*-

from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG

class ClientStoppedMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.CLIENT_STOPPED
    ack = True
    
    def trigger(self, message):
        return message.streamid == self.stream.id


    def action(self, message, peer):
            self.log.debug('received clientStopped message from %s',peer)
            self.overlay.removeNeighbour(peer)
            found=False
            for ov in self.overlays.values():
                if ov.isNeighbour(peer):
                    found=True
                    break
            if not found:
                self.log.debug('remove %s from known peers',peer)
                self.knownPeers.remove(peer)