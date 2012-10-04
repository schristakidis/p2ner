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
