# -*- coding: utf-8 -*-

from p2ner.abstract.engine import Engine
from p2ner.core.components import loadComponent
from p2ner.base.messages.bootstrap import ClientStartedMessage
from messages.messageobjects import RequestStreamMessage
from messages.streammessage import StreamMessage 
from p2ner.base.Peer import Peer
from twisted.internet import reactor

defaultStream = ("StreamClient", [], {})

class Client(Engine):
    
    def initEngine(self, server="127.0.0.1"):
        self.enableTraffic()
        self.enableControlUI()
        self.server = Peer(server, 16000)
        self.messages = []
        self.messages.append(StreamMessage())
        self.streams = []
        
        
    def start(self, sid, streamResource=None):
        reactor.callLater(0.1, ClientStartedMessage.send, self.traffic.port, self.server, self.controlPipe)
        reactor.callLater(0.5, RequestStreamMessage.send, sid, self.server, self.controlPipe)
        
    
    def newStream(self, stream, streamResource=None):
        if self.getStream(stream.id):
            raise ValueError("Stream already exists")
        if not streamResource:
            streamResource = defaultStream
        if streamResource:
            s, a, k = streamResource
            k["stream"] = stream
            stream = loadComponent("stream", s)
            self.streams.append(stream(_parent=self, *a, **k))



if __name__ == "__main__":
    P2NER = Client()
    reactor.run()
