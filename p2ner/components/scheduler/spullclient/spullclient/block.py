# -*- coding: utf-8 -*-

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
        if not self.scheduler.running:
            #print "RESUSCITATE SCHEDULER"
            self.scheduler.running = True
            self.scheduler.produceBlock()
            