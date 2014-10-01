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

# -*- coding: utf-8 -*-

import random
from twisted.internet import reactor, task,defer
from p2ner.abstract.plugin import Plugin
from p2ner.core.namespace import Namespace
from p2ner.base.Peer import Peer




class FlowBwMeasurement(Plugin):

    def initPlugin(self,server,**kwargs):
        self.server=Peer(server[0],dataPort=16001)
        self.stream = Namespace(self)
        self.stream.id = random.randint(1,32000)
        self.root.trafficPipe.registerProducer(self)
        fragmentSize=1408
        numberOfFragments=10
        blockSize=fragmentSize*numberOfFragments
        bufferSize=3
        self.blocks = []
        self.loop = task.LoopingCall(self.shift)
        self.blockdata = "".join([chr(random.randint(0, 255)) for i in xrange(blockSize)])
        self.firstblock = 0
        self.lastblock = 0
        for i in range(bufferSize):
            self.shift(False)

    def start(self):
        self.d=defer.Deferred()
        self.loop.start(0.1)
        self.log.log(15,"measuring BW")
        return self.d


    def produceBlock(self):
        return

    def shift(self, sendblk=True):
        cap=self.root.trafficPipe.callSimple('getReportedCap')
        if self.root.trafficPipe.callSimple('getReportedCap'):
            self.finished(cap)
            return
        self.lastblock += 1
        self.trafficPipe.call("inputblock", self, self.lastblock, self.blockdata)
        if sendblk:
            self.firstblock += 1
            self.trafficPipe.call("sendblock", self, self.firstblock, self.server)
            self.trafficPipe.call("popblockdata", self, self.firstblock-1)

    def finished(self,cap):
        self.log.log(15,'Bandwidth is:%s KB/sec'%str(cap))
        reactor.callLater(2,self.log.log,15,'')
        self.loop.stop()
        for i in range(self.firstblock,self.lastblock+1):
            self.trafficPipe.call("popblockdata",self,i)
        self.trafficPipe.unregisterProducer(self)
        self.d.callback(cap)

