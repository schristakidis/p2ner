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


from time import time
from p2ner.base.BlockMessage import BlockMessage

class Block(BlockMessage):
    type = "blockfragment"
    
    def trigger(self, block):
        if block.streamid == self.stream.id:
            return True
        return False
      
    def action(self, block, peer):
        #print 'recived fragment ',fragment.blockid,' from ',peer,' lpb ',self.buffer.lpb
        if not self.loopingCall.running:
            return
            self.scheduler.start()
        while block.blockid > self.buffer.lpb:
            #print '??????????????????????????????????????????????'
            self.scheduler.shift(norequests=True) 
        #print fragment.blockid,fragment.fragmentid,fragment.fragments
        self.scheduler.buffer.updateBlock(block.blockid)
        #if not self.scheduler.running: #probably just for the push scheduler
            #print "RESUSCITATE SCHEDULER"
            #self.scheduler.running = True
            #self.scheduler.produceBlock()
            