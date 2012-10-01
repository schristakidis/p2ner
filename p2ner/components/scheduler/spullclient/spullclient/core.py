# -*- coding: utf-8 -*-

from twisted.internet import task, reactor
from twisted.internet.threads import deferToThread
from random import choice, uniform
from time import time
from p2ner.abstract.scheduler import Scheduler
from p2ner.base.Buffer import Buffer
from p2ner.base.BufferList import getMostDeprivedReq
from messages.buffermessage import BufferMessage
from messages.lpbmsg import LPBMessage
from messages.messageobjects import ClientStoppedMessage
from messages.retransmitmessage import RetransmitMessage
from block import Block

EXPIRE_TIME = 0.5

def requestOne(requests):
    blocksToRequest = {}
    for peer in requests:
        if len(requests[peer]) > 1:
            blocksToRequest[peer] = [choice(requests[peer])]
        else:
            blocksToRequest[peer] = requests[peer]
    return blocksToRequest

class SPullClient(Scheduler):
    
    def registerMessages(self):
        self.messages = []
        self.messages.append(BufferMessage())
        self.messages.append(LPBMessage())
        self.messages.append(RetransmitMessage())
        self.blocks = []
        self.blocks.append(Block())
    
    def initScheduler(self):
        self.log.info('initing scheduler')
        self.running = False
        self.registerMessages()
        self.loopingCall = task.LoopingCall(self.shift)
        self.reqInterval=self.stream.scheduler['reqInt']
        self.frequency = 1.0/self.stream.scheduler['blocksec']
        self.buffer = Buffer(buffersize=self.stream.scheduler['bufsize'],log=self.log)
    
    def errback(self, failure): return failure

    def produceBlock(self):
        #print "PRODUCEBLOCK"
        d = deferToThread(self.getRequestedBID)
        d.addCallback(self.sendBlock)
        d.addErrback(self.errback)
        return d
        
    def sendBlock(self, req):
        if not req:
            self.running = False
            return None
        bid, peer = req
        #self.log.debug('sending block %d to %s',bid,peer)
        self.trafficPipe.call("sendblock", self, bid, peer)
        
    def getRequestedBID(self):
        #print "GETREQUESTEDBID"
        while True:
            #print self.bufferlist
            peer = getMostDeprivedReq(self.bufferlist, self.buffer)
            if peer is None:
                self.running = False
                #print "STOP SERVING\n\n"
                return None
            bl = self.buffer.bIDListCompTrue(peer.s[self.stream.id]["request"])
            if len(bl) > 0:
                blockID = choice(bl)
                peer.s[self.stream.id]["request"].remove(blockID)
                peer.s[self.stream.id]["buffer"].update(blockID)
                #print "SENDING BLOCK", blockID, peer
                peer.s[self.stream.id]["luck"] = blockID
                return (blockID, peer)
            else:
                peer.s[self.stream.id]["request"]=[]
        
    def start(self):
        self.log.info('scheduler is starting')
        self.loopingCall.start(self.frequency)
        
    def stop(self):
        self.log.info('scheduler is stopping')
        self.log.debug('sending clientStopped message to %s',self.server)
        ClientStoppedMessage.send(self.stream.id, self.server, self.controlPipe)
        for n in self.overlay.getNeighbours():
            self.log.debug('sending clientStopped message to %s',n)
            ClientStoppedMessage.send(self.stream.id, n, self.controlPipe)
        #reactor.callLater(0, self.stream.stop)
        try:
            self.loopingCall.stop()
        except:
            pass
         
         
    def makeRequests(self, receivingBlocks, missingBlocks, neighbours):
        #print 'neighbours:',neighbours
        #print "COMPUTING REQUESTS"
        #print missingBlocks
        #exclude receiving
        def dd(self, receivingBlocks, missingBlocks, neighbours):
            for bid in missingBlocks:
                if bid in receivingBlocks:
                    missingBlocks.remove(bid)
                elif bid < self.buffer.flpb:
                    missingBlocks.remove(bid)
            #print 'missing blocks:',missingBlocks
            tmpBlocksToRequest = {}
            requestableBlocks = {}
            for peer in neighbours:
                if self.stream.id not in peer.s:
                    print str(self.stream.id), 'in cotinue 1', peer, peer.s
                    print neighbours
                    continue
                if "buffer" not in peer.s[self.stream.id]:
                    print 'in continue 2'
                    continue
                buffer = peer.s[self.stream.id]["buffer"]
                #print 'neigh buffer:',buffer
                tempReq = buffer.bIDListCompTrue(missingBlocks)
                tmpBlocksToRequest[peer] = tempReq
                #print 'temp:',tempReq
                for b in tempReq:
                    if b in requestableBlocks:
                        requestableBlocks[b].append(peer)
                    else:
                        requestableBlocks[b] = [peer]
            keys = tmpBlocksToRequest.keys()
            blocksToRequest = {}
            for k in keys:
                blocksToRequest[k] = []
            #take out blocks with only 1 source
            reqBlockList = requestableBlocks.keys()
            for b in reqBlockList:
                if len(requestableBlocks[b]) == 1:
                    peer = requestableBlocks[b][0]
                    blocksToRequest[peer].append(b)
                    del requestableBlocks[b]
            #while There are blocks to request
            while len(requestableBlocks) > 0:
                #get the block with less sources
                block = min([ (len(requestableBlocks[x]),x) for x in requestableBlocks])[1]
                #get the peer with min(less possible requests, less requests so far)
                peer = min([ (min(len(tmpBlocksToRequest[x]),len(blocksToRequest[x])),x) for x in tmpBlocksToRequest if block in tmpBlocksToRequest[x]])[1]
                del requestableBlocks[block]
                blocksToRequest[peer].append(block)
            #print "BLOCKSTOREQUESTSSSS", blocksToRequest
            peerWithRequests = 0
            for peer in blocksToRequest:
                if len(blocksToRequest[peer]):
                    peerWithRequests+=1
            if peerWithRequests > self.reqInterval:
                blocksToRequest = requestOne(blocksToRequest)
            return blocksToRequest
        return deferToThread(dd, self, receivingBlocks, missingBlocks, neighbours)
        #return dd(self, receivingBlocks, missingBlocks, neighbours)
        
    def sendRequests(self, requests):
        for peer in self.overlay.getNeighbours():
            reactor.callLater(uniform(0,0.05), BufferMessage.send, self.stream.id, self.buffer, requests.get(peer), peer, self.controlPipe)
    
    def sendLPB(self, peer):
        self.log.warning('sending LPB message to %s',peer)
        LPBMessage.send(self.stream.id, self.buffer.lpb, peer, self.controlPipe)
        
    def shift(self, norequests = False):
        n = self.overlay.getNeighbours()
        outID = self.buffer.shift()

        if not norequests:
            #send buffers
            if self.buffer.lpb % self.reqInterval == 0:
                d = self.trafficPipe.call("getreceiving", self)
                d.addCallback (self.makeRequests, self.buffer.getFalseBIDList(), n)
                d.addCallback(self.sendRequests)
                d.addErrback(self.errback)
            else:
                #print 'sending buffer'
                reactor.callLater(uniform(0,0.05), BufferMessage.send, self.stream.id, self.buffer, None, n, self.controlPipe)
        
        #self.log.debug('%s',self.buffer)
        #print self.buffer
        #push block to output

        outdata = self.trafficPipe.call("popblockdata", self, outID)
        outdata.addCallback(self.output.write)


    def isRunning(self):
        return self.loopingCall.running
    
    def askFragments(self,bid,fragments,peer):
        print 'should ask from ',peer,fragments,bid
        RetransmitMessage.send(self.stream.id,fragments,bid,peer,self.controlPipe)

    def retransmit(self,block,fragments,peer):
        print 'should retransmit to ',peer,block,fragments
        b={}
        b['blockid']=block
        b['fragments']=fragments
        self.trafficPipe.call('sendFragments',self,b,peer)
        
