# -*- coding: utf-8 -*-
#   Copyright 2013 Loris Corazza, Sakis Christakidis
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


from p2ner.abstract.pipeelement import PipeElement
from twisted.internet import reactor,task
from p2ner.base.Peer import Peer
from p2ner.base.BlockMessage import BlockMessage
from random import choice
from construct import Container
from p2ner.core.components import loadComponent
import bora
import pprint


class Block(object):
    type = "blockfragment"

def triggerblk(totrigger, message):
    triggered = []
    for b in totrigger:
        if b.trigger(message):
            triggered.append(b)
    return triggered

def scanBlocks(message):
    instances = BlockMessage.getInstances()
    triggered = triggerblk(instances, message)
    return triggered

def biter_thread(pipe):
    for b in bora.biter():
        # print "block", b, "RECV"
        block = Container(streamid=b[0], blockid=b[1])
        #print "BITER BLOCK",block
        r = scanBlocks(block)
        reactor.callFromThread(pipe.triggerActions, r, block)

def bpuller_thread(pipe):
    for b in bora.bpuller():
        #print "Asking for data to send"
        reactor.callFromThread(pipe.produceblock)

class BoraElement(PipeElement):

    def initElement(self, port=30000, to='dataPort', **kwargs):
        self.log.info('BoraElement loaded')
        self.to = to
        self.port = port
        self.schedulers = {}
        flowControl = loadComponent('flowcontrol', 'DistFlowControl')
        self.flowControl = flowControl(_parent=self)
        reactor.addSystemEventTrigger('before', 'shutdown', bora.die)


    def sendblock(self, r, scheduler, block, peer):
        print "SENDBLOCK"
        if scheduler not in self.schedulers:
            self.log.error("scheduler for stream id %d is not registered to the pipeline" % scheduler.stream.id)
            return

        to=self.to

        useLocalIp=False
        try: #for the server
            if self.root.netChecker.nat and peer.ip==self.root.netChecker.externalIp:
                useLocalIp=True
                peer.useLocalIp=True
        except:
            pass

        if peer.useLocalIp:
            ip=peer.lip
            to='l'+to
        else:
            ip=peer.ip

        reactor.callLater(0, bora.send_block, scheduler.stream.id, block, ip, getattr(peer, to))
        return 0

    def getreceiving(self, r, scheduler):
        if scheduler not in self.schedulers:
            self.log.error("scheduler for stream id %d is not registered to the pipeline" % scheduler.stream.id)
            return
        incomplete = bora.incomplete_block_list()
        #print "incomplete:", incomplete
        if len(incomplete):
            incomplete = [i for i in incomplete if incomplete[0]==scheduler.stream.id]
        #print "incomplete2", incomplete
        return incomplete

    def popblockdata(self, r, scheduler, blockid):
        if scheduler not in self.schedulers:
            self.log.error("scheduler for stream id %d is not registered to the pipeline" % scheduler.stream.id)
            return
        ret = bora.get_block_content (scheduler.stream.id, blockid)
        reactor.callLater(0, bora.del_block, scheduler.stream.id, blockid-1)
        return ret

    def inputblock(self, r, scheduler, bid, data):
        if scheduler not in self.schedulers:
            self.log.error("scheduler for stream id %d is not registered to the pipeline" % scheduler.stream.id)
            return
        reactor.callLater(0, bora.add_block, scheduler.stream.id, bid, data)

    def listen(self, d):

        bora.listen_on(self.port)
        self.log.info('start listening to port:%d',self.port)

        print 'listening to port  ',self.port
        reactor.callInThread(biter_thread, self)
        reactor.callInThread(bpuller_thread, self)
        self.flowControl.start()

    def getscheduler(self, streamid):
        ret = None
        streamid = int(streamid)
        for s in self.schedulers:
            try:
                if streamid == int(s.stream.id):
                    return s
            except:
                print "uninitialized scheduler"
        return ret

    def registerScheduler(self, r, scheduler):
        if self.getscheduler(scheduler.stream.id):
            raise IndexError("You don't want to stream and subscribe the same stream")
        else:
            self.schedulers[scheduler] = {}

    def unregisterScheduler(self, r, scheduler):
        if scheduler in self.schedulers:
            del self.schedulers[scheduler]
        else:
            raise IndexError("There is no such scheduler to unregister")

    def produceblock(self, r=None):
        #print "PRODUCEBLOCK"
        '''
        remove this and make a new el for more sophisticated scheduler prio selection
        '''
        sl = self.schedulers.keys()
        if len(sl):
            s = choice(sl)
            #print "CALLING SCHEDULER"
            reactor.callLater(0, s.produceBlock)

    def triggerActions(self, scannedblocks, message, peer=None):
        for b in scannedblocks:
            b.action(message, peer)

    def cleanUP(self):
        bora.die()
        self.schedulers = {}

    def getBW(self):
        return 100

    def getPort(self):
        return self.port

