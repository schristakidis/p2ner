# -*- coding: utf-8 -*-

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
