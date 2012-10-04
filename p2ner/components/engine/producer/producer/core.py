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
    
