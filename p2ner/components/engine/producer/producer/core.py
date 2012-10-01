# -*- coding: utf-8 -*-

from p2ner.abstract.engine import Engine
from p2ner.core.components import loadComponent
from p2ner.base.messages.bootstrap import ClientStartedMessage
from messages.streammessage import StreamMessage, StreamIdMessage
from twisted.internet import reactor
from p2ner.base.Peer import Peer


defaultStream = ("StreamProducer", [], {})


class Producer(Engine):
    
    def initEngine(self, server="127.0.0.1", **kwargs):
        self.enableTraffic()
        self.streams = []
        self.server = Peer(server, 16000)
        self.sidListeners = []
        self.start2()
        
    def start2(self):
        reactor.callLater(0.1, ClientStartedMessage.send, self.traffic.port, self.server, self.controlPipe)        
    
    def start(self, stream):
        reactor.callLater(0.1, ClientStartedMessage.send, self.traffic.port, self.server, self.controlPipe)
        self.sidListeners.append(StreamIdMessage(stream))
        reactor.callLater(0.5, StreamMessage.send, stream, self.server, self.controlPipe) 
    
    def newStream(self, stream):
        if defaultStream:
            s, a, k = defaultStream
            k["stream"] = stream
            stream = loadComponent("stream", s)
            self.streams.append(stream(_parent=self, *a, **k))

if __name__ == "__main__":
    P2NER = Producer(control = ("UDPCM", [], {"port":51000}))
    reactor.run()
    
