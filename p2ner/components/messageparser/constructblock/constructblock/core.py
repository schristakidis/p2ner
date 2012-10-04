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


from p2ner.abstract.messageparser import MessageParser
from twisted.internet.threads import deferToThread
from decodeblocks import scanBlocks
from encodeblocks import encodeblock

class ConstructBlockParser(MessageParser):
    
    def errback(self, failure): return failure

    def initMessageparser(self, *args, **kwargs):
        self.log.info('ConstructMessage loaded')
    
    def encode(self, msg, content):
        return encodeblock(msg, content)
        d = deferToThread(encodeblock, msg, content)
        d.addErrback(self.errback)
        return d
    
    def decode(self, message, peer):
        d = deferToThread(scanBlocks, message,peer)
        d.addCallback(self.triggerActions)
        d.addErrback(self.errback)
        return d
        
    def triggerActions(self, scannedblocks):
        peer=scannedblocks[1]
        scannedblocks=scannedblocks[0]
        for b in scannedblocks:
            b[0].action(b[1], peer)
