# -*- coding: utf-8 -*-

from p2ner.abstract.pipeline import Pipeline
from p2ner.core.components import loadComponent
from construct import Container
from p2ner.base.Peer import Peer

class MsgPipe(Pipeline):
    
    def initPipeline(self, *args, **kwargs):
        self.log.info('MsgPipe loaded')
    
    def send(self, msg, content, peer):
        if isinstance(peer, (list, tuple)):
            pass
        else:
            peer = [peer]
        content.header = Container(ack=msg.ack, code=msg.code, port=self.control.port)

        d = self.messageparser.encode(msg, content)
        for p in peer:
            d.addCallback(self.control.send, p)
    
    def receive(self, data, (host, port)):
        p = (host, port)
        #print host, port, len(data)
        self.messageparser.decode(data, p)
