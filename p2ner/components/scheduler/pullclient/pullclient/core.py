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


from twisted.internet import task
from twisted.internet.threads import deferToThread
from random import choice
from time import time
from p2ner.abstract.scheduler import Scheduler
from p2ner.base.Buffer import Buffer
from p2ner.base.BufferList import getMostDeprivedReq,getRarestRequest
from messages.buffermessage import BufferMessage
from messages.lpbmsg import LPBMessage
from messages.retransmitmessage import RetransmitMessage
from block import Block
from p2ner.core.statsFunctions import counter, setLPB,setValue
import networkx as nx

EXPIRE_TIME = 0.5

class PullClient(Scheduler):

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
        self.countHit=0
        self.countMiss=0
        self.startTime=0
        self.idleTime=0
        self.lastIdleTime=0
        self.lastReqCheck=0
        self.requestFrequency=self.frequency*self.reqInterval

    def errback(self, failure): return failure

    def produceBlock(self):
        # print "IN SCHEDULER PRODUCEBLOCK"
        #self.log.debug('trying to produce block')
        self.running=True
        d = deferToThread(self.getRequestedBID)
        d.addCallback(self.sendBlock)
        d.addErrback(self.errback)
        return d

    def sendBlock(self, req):
        # print "in SCHEDULER sendblock"
        if not req:
            self.running = False
            if not self.lastIdleTime:
                self.lastIdleTime=time()
            # print "NOT SENDING"
            #self.log.warning('no blocks to send. stopping scheduler')
            return None
        if self.lastIdleTime:
            tempidle=time()-self.lastIdleTime
            self.idleTime +=tempidle
            #self.log.debug('idle for %f',tempidle)
            self.lastIdleTime=0
        self.running=True
        bid, peer = req
        self.log.debug('sending block %d to %s',bid,peer)
        # print 'sending block %d to %s'%(bid,peer)
        self.trafficPipe.call("sendblock", self, bid, peer)
        counter(self, "blocksent")

    def getRequestedBID(self):
        # print "GETREQUESTEDBID"
        while True:
            #print self.bufferlist
            peer = getMostDeprivedReq(self.bufferlist, self.buffer)
            if peer is None:
                self.running = False
                #print "STOP SERVING\n\n"
                #self.log.warning('no deprived peer')
                self.lastReqCheck=time()
                return None
            #self.log.debug('requests from most deprived %s %s',peer,peer.s[self.stream.id]["request"])
            bl = self.buffer.bIDListCompTrue(peer.s[self.stream.id]["request"])
            bl2=bl[:]
            # print "BL:", bl
            #self.log.debug('possible blocks to send %s',bl)
            if len(bl) > 0:
                #blockID = choice(bl)
                rarest=False

                try:
                    blockID=getRarestRequest(self.bufferlist,self.buffer,bl)
                    rarest=True
                except:
                    blockID = choice(bl)

                #blockID=bl[0]
                try:
                    peer.s[self.stream.id]["request"].remove(blockID)
                    peer.s[self.stream.id]["buffer"].update(blockID)
                except:
                    self.log.error("problem in scheduler. Can't remove blockid %s"%blockID)
                    self.log.error("blocks:%s,requests:%s,blocks before:%s"%(bl,peer.s[self.stream.id]["request"],bl2))
                    self.log.error("happened while searching for rarest:%s"%rarest)
                    continue
                print "SENDING BLOCK", blockID, peer
                self.lastReqCheck=time()
                return (blockID, peer)
            else:
                print 'sending nothing'
                peer.s[self.stream.id]["request"]=[]


    def start(self):
        self.startTime=time()
        self.idleTime=0
        self.lastIdleTime=0
        self.countHit=0
        self.countMiss=0
        self.log.info('scheduler is starting')
        self.loopingCall.start(self.frequency)
        self.trafficPipe.call('resetIdleStat')

    def stop(self):
        self.log.info('scheduler is stopping')
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
        # print "MISSING", missingBlocks
        print "RECEIVING", receivingBlocks
        def dd(self, receivingBlocks, missingBlocks, neighbours):
            if not neighbours:
                return
            for bid in missingBlocks:
                if bid in receivingBlocks:
                    missingBlocks.remove(bid)
            ######
            #TODO: manage lpb0
            ######
            #print 'missing blocks:',missingBlocks
            tmpBlocksToRequest = {}
            requestableBlocks = {}
            ids={}
            countIds=0
            for peer in neighbours:
                if self.stream.id not in peer.s:
                    print 'in cotinue 1'
                    continue
                if "buffer" not in peer.s[self.stream.id]:
                    print 'in continue 2'
                    continue
                buffer = peer.s[self.stream.id]["buffer"]
                # print "BUFFER", buffer
                #print 'neigh buffer:',buffer
                tempReq = buffer.bIDListCompTrue(missingBlocks)
                tmpBlocksToRequest[peer] = tempReq
                #print 'temp:',tempReq
                for b in tempReq:
                    if b in requestableBlocks:
                        requestableBlocks[b].append(peer)
                    else:
                        requestableBlocks[b] = [peer]
                ids[peer]='p'+str(countIds)
                countIds+=1

            if not requestableBlocks:
                return {}

            """
            blocksToRequest={}
            for p in neighbours:
                blocksToRequest[p]=[]


            while True:

                reqBlockList = requestableBlocks.keys()
                for b in reqBlockList:
                    if len(requestableBlocks[b]) == 1:
                        peer = requestableBlocks[b][0]
                        blocksToRequest[peer]+=[b]
                        del requestableBlocks[b]

                G=nx.DiGraph()
                for b,peers in requestableBlocks.items():
                    G.add_edge('s',b,capacity=1)
                    for p in peers:
                        G.add_edge(b,ids[p],capacity=1)#,weight=len(peers))

                for id in ids.values():
                    G.add_edge(id,'e')#,capacity=1)


                try:
                    flow, F = nx.ford_fulkerson(G, 's', 'e')
                    #F=nx.max_flow_min_cost(G,'s','e')
                except:
                    self.log.error('scheduler matching failed')

                for peer,id in ids.items():
                    blocksToRequest[peer] +=[b for b in F.keys() if b in requestableBlocks.keys() and  F[b].has_key(id) and int(F[b][id])==1]


            """
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
            #self.log.debug('requesting blocks %s',blocksToRequest)
            return blocksToRequest
        return deferToThread(dd, self, receivingBlocks, missingBlocks, neighbours)
        #return dd(self, receivingBlocks, missingBlocks, neighbours)


    def sendRequests(self, requests):
        for peer in self.overlay.getNeighbours():
            r= requests.get(peer)
            #self.log.debug('sending requests to %s %s',peer,r)
            print('sending requests to %s %s',peer,r)
            BufferMessage.send(self.stream.id, self.buffer, r, peer, self.controlPipe)

    def sendLPB(self, peer):
        self.log.warning('sending LPB message to %s',peer)
        LPBMessage.send(self.stream.id, self.buffer.lpb, peer, self.controlPipe)

    def shift(self, norequests = False):
        n = self.overlay.getNeighbours()
        outID,hit = self.buffer.shift()
        setLPB(self, self.buffer.lpb)

        if self.buffer.lpb - self.buffer.flpb > self.buffer.buffersize:
            if not hit:
                self.countMiss +=1
            else:
                self.countHit +=1
            hitRatio=self.countHit/float(self.countHit+self.countMiss)
            setValue(self,'scheduler',hitRatio*1000)
            #self.log.debug('hit ratio %f',hitRatio)


        if not norequests:
            #send buffers
            if self.buffer.lpb % self.reqInterval == 0:
                d = self.trafficPipe.call("getreceiving", self)
                d.addCallback (self.makeRequests, self.buffer.getFalseBIDList(), n)
                d.addCallback(self.sendRequests)
                d.addErrback(self.errback)
            else:
                #print 'sending buffer'
                BufferMessage.send(self.stream.id, self.buffer, None, n, self.controlPipe)

        #self.log.debug('%s',self.buffer)

        idleRatio=self.idleTime/(time()-self.startTime)
        #self.log.debug('idle:%f',idleRatio)
        setValue(self,'idle',idleRatio*1000)
        #print self.buffer
        #push block to output

        outdata = self.trafficPipe.call("popblockdata", self, outID)
        outdata.addCallback(self.output.write)


    def isRunning(self):
        return self.loopingCall.running

    def askFragments(self,bid,fragments,peer):
        print 'should ask from ',peer,fragments,bid
        self.log.warning('should ask from %s,%s,%d',peer,fragments,bid)
        RetransmitMessage.send(self.stream.id,fragments,bid,peer,self.controlPipe)

    def retransmit(self,block,fragments,peer):
        print 'should retransmit to ',peer,block,fragments
        self.log.warning('should retransmit to %s,%d,%s',peer,block,fragments)
        b={}
        b['blockid']=block
        b['fragments']=fragments
        self.trafficPipe.call('sendFragments',self,b,peer)

