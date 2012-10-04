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
