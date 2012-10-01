# -*- coding: utf-8 -*-

from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from random import choice
from p2ner.abstract.pipeline import Pipeline
from p2ner.base.Peer import Peer
from construct import Container

class Fragment(object):
    type = "blockfragment"


class BlockPipe(Pipeline):

    def errback(self, failure): return failure

    def initPipeline(self, rate=750000, MTU=1400):
        self.running = False
        self.rate = rate
        self.MTU = MTU
        self.queue = []
        self.sentBytesSincePause = 0
        self.log.info('BlockPipe loaded')
        
    def send(self, block, content, peer):
        if not isinstance(peer, (list, tuple)):
            peer = [peer]
            
        content.header = Container(port=self.traffic.port)
        if block.type != "blockfragment" and block.type != "md5blockfragment":
            d = deferToThread(self.splitblock, block, content)
        elif len(content.data) > self.MTU:
            self.log.error("Block data bigger than MTU")
            raise("Block data bigger than MTU")
        else:
            d = deferToThread(self.encode, block, content)
        d.addCallback(self.enqueue, block, peer)
        d.addCallback(self.queueUnlock)
        d.addErrback(self.errback)
    
    def enqueue(self, content, block, peer):
        if not isinstance(peer, (list, tuple)):
            peer = [peer]
        for p in peer:
            if not isinstance(content, list):
                content = [content]
            for c in content:
                self.queue.append((block, c, p))
        return 
        
    def queueUnlock(self, ret):
        if self.running:
            return
        self.running=True
        self.deliverNext()
        return
            
    def splitblock(self, block, content):
        ret = []
        f = self.split_len(content.data, self.MTU)
        flen = len(f)
        for i in range(flen):
            c=Container(streamid=content.streamid, blockid=content.blockid, data=f[i], fragmentid=i, fragments=flen)
            c.header= Container(port=self.traffic.port)
            ret.append(self.blockparser.encode(Fragment,c ))
        return ret
        
    def encode(self, block, content):
        ret = self.blockparser.encode(block, content)
        return ret
        
    def split_len(self, seq, length):
        return [seq[i:i+length] for i in range(0, len(seq), length)]
    
    def deliverNext(self):
        if len(self.queue)==0:
            self.running=False
            return
        if len(self.queue)<2:
            self.produceBlock()
        block, content, peer = self.queue.pop(0)
        l = len(content)
        nextiter = 1.0*l/self.rate
        self.traffic.send(content, peer)
        reactor.callLater(nextiter, self.deliverNext)
        
    def produceBlock(self):
        for producer in self.producers:
            if not producer():
                self.producers.remove(producer)
        activeproducers = [p() for p in self.producers if p().running]
        if len(activeproducers):
            p = choice(activeproducers)
            p.produceBlock()
        
    def receive(self, data, (host, port)):
        p=(host, port)
        #print "RECVVV", len(data), host, port
        self.blockparser.decode(data, p)
