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


from p2ner.abstract.pipeelement import PipeElement
from twisted.internet import reactor,task
from p2ner.base.Peer import Peer
from collections import deque
import time
from p2ner.core.statsFunctions import setValue

class BandwidthElement(PipeElement):

    def initElement(self, bw=200000):
        self.log.info('ControlBandwidthElement loaded')
        self.bw = bw
        self.que = deque()
        self.stuck = True
        self.countBytes=0
        self.loopingCall=task.LoopingCall(self.writeStat)
        self.loopingCall.start(2)
        
    def send(self, res, msg, data, peer):
        if isinstance(res, (list, tuple)):
            for r in res:
               pack = (r, peer)
               self.que.append(pack)
        else:
            pack = (res, peer)
            self.que.append(pack)
        if self.stuck:
            self.stuck = False
            reactor.callLater(0, self.sendfromque)
        self.breakCall()
        return res
    
    def sendfromque(self):
        if len(self.que) == 0:
            self.stuck = True
            return
        res, peer = self.que.popleft()
        bw=self.bw
        
        self.countBytes +=len(res)    
        nextiter=1.0*len(res)/bw
        #print 'next iter:',nextiter
        reactor.callLater(nextiter, self.sendfromque)
        #print 'next:',nextiter
        #print 'total:',time.time()+nextiter
        self.forwardnext("send", None, None, peer).callback(res)
        

    def writeStat(self):
        setValue(self,'controlover',self.countBytes*8/(2.0))
        self.countBytes=0
