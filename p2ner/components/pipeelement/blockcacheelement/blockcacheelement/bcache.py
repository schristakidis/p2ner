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
from twisted.internet.threads import deferToThread
from construct import Container
import weakref
from p2ner.base.BlockMessage import BlockMessage
from random import choice
import time
from messages.rttmessage import RTTMessage

class Fragment(object):
    type = "blockfragment"
    
class Block(object):
    type = "blockfragment"

def triggerblk(totrigger, message):
    triggered = []
    for b in totrigger:
        if b.trigger(message):
            triggered.append(b)
    return triggered
    
def scanBlocks(message, peer):
    instances = BlockMessage.getInstances()
    triggered = triggerblk(instances, message)
    return triggered

class CBlock(object):
    def __init__(self, sid, blocknumber, nfragments):
        self.fragments = {}
        self.nfragments = nfragments
        self.block = Container(streamid=sid, blockid=blocknumber, data="")
        self.streamid = sid
        self.retransmited=False
        
    @property
    def data(self):
        return self.block.data
        
    def receive(self, encodedfragment, fragment, peer=None):
        dup=False
        if self.fragments.has_key(fragment.fragmentid):
            print 'duplicate fragmentttttt ', self.block['blockid'], fragment.fragmentid
            dup=True
        else:
            self.fragments[fragment.fragmentid] = (encodedfragment, fragment, peer)
        ret = self.complete
        if ret and not dup:
            self.setblockdata()
        return ret
        
    def getLenBlockData(self):
        ret=0
        for f in self.fragments.values():
            ret +=len(f[0])
        return ret
    
    def fill(self):
        return 1.0*len(self.fragments)/self.nfragments
    
    def getBlockData(self):
        ret = ""
        if self.block.data:
            return self.block.data
        for fid in sorted(self.fragments.keys()):
            ret = "".join([ret, self.fragments[fid][1].data])
        return ret
        
    def setblockdata(self):
        for fid in sorted(self.fragments.keys()):
            self.block.data = "".join([self.block.data, self.fragments[fid][1].data])
            
    def getLenNBlockData(self):
        ret=0
        for f in range(self.nfragments-1):
            ret +=len(self.fragments[f][0])
        return ret
    
    @property
    def complete(self):
        if self.nfragments == len(self.fragments):
            return True
        return False

class BlockCache(PipeElement):

    def initElement(self, timeout=0.1):
        self.log.info('BlockCacheElement loaded')
        self.schedulers = {} #weakref.WeakKeyDictionary()
        self.timeout = timeout
        self.receiving={}
        self.loopingCall = task.LoopingCall(self.checkLost)
        self.loopingCall.start(self.timeout)
        
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
        
    def sendblock(self, r, scheduler, block, peer):
        '''
        To be called from the scheduler to send a block
        '''
        enc=[]
        if block in self.schedulers[scheduler]:
            b = self.schedulers[scheduler][block]
            for f in b.fragments:
                encoded, decoded, p = b.fragments[f]
                d = self.forwardnext("send", Fragment, decoded, peer)
                enc.append(encoded)
            d.callback((enc,0))
            return True
        return False
    
    def sendFragments(self, r, scheduler, block, peer):
        '''
        To be called from the scheduler to send a block
        '''
        enc=[]
        blockid=block['blockid']
        fragments=block['fragments']
        print 'retransmitinggggggggggg to ',peer,blockid,fragments
        if blockid in self.schedulers[scheduler]:
            b = self.schedulers[scheduler][blockid]
            failedFragments=len(fragments)*1.0/b.nfragments
            for f in fragments:
                frag=b.fragments[f]
                encoded, decoded, p = frag
                d = self.forwardnext("send", Fragment, decoded, peer)
                enc.append(encoded)
            d.callback((enc,failedFragments))
            return True
        return False
    
    def popblockdata(self, r, scheduler, blockid):
        '''
        To be called from the scheduler when shifting to erase a block from the cache and retrieve it's data for the output
        '''
        if blockid not in self.schedulers[scheduler]:
            return ""
    
        b = self.schedulers[scheduler].pop(blockid)
        if not b.complete:
            print 'expiredddddddddddd 2222222',blockid
            print b.fragments.keys()
            print b.nfragments
        ret = b.getBlockData()
        return ret
    
    def inputblock(self, r, scheduler, bid, data): 
        '''
        To be called from the scheduler when data is read from the input to put a block in the cache
        '''
        nfragments = len(r)
        b = self.schedulers[scheduler][bid] = CBlock(scheduler.stream.id, bid, nfragments)
        for f in r:
            b.receive(*f)
        return r
    
    def getreceiving(self, r, scheduler):
        '''
        To be called from the scheduler to know which blocks are being received
        '''
        ret = []
        if scheduler not in self.schedulers:
            return ret
        for b in self.schedulers[scheduler]:
            if self.schedulers[scheduler][b].fill() < 1.0:
                ret.append(b)
        return ret
    
    def receive(self, encodedfragment, peer,bw,recTime, sendTime):
        d = self.forwardprev("decodefragment", encodedfragment)
        d.addCallback(self.updateBlock, encodedfragment, peer, bw, recTime, sendTime)
        reactor.callLater(0, d.callback, Fragment)
        return d
        
        
    def updateBlock(self, ret, encodedfragment, peer, bw,recTime,sendTime):
        s = self.getscheduler(ret.streamid)
        if s is None:
            self.breakCall()
        if ret.blockid not in self.schedulers[s]:
            self.schedulers[s][ret.blockid] = CBlock(ret.streamid, ret.blockid, ret.fragments)
            
            self.receiving[ret.blockid]=s
            
            self.schedulers[s][ret.blockid].sendTime=sendTime
            self.schedulers[s][ret.blockid].peer=peer
            self.schedulers[s][ret.blockid].receivedTime=recTime
            self.schedulers[s][ret.blockid].rate=bw
            self.schedulers[s][ret.blockid].times=[]
            self.schedulers[s][ret.blockid].times.append(recTime)
            self.schedulers[s][ret.blockid].lastReceived=recTime
            self.schedulers[s][ret.blockid].retr=False
            #print 'STT:',time.time()-recTime,bw,ret.fragments
        else:
            self.schedulers[s][ret.blockid].times.append(recTime)
            self.schedulers[s][ret.blockid].lastReceived=recTime

            if self.schedulers[s][ret.blockid].retr:
                print 'received retransmitted fragment'
                print ret.blockid
                print ret.fragmentid
                print recTime
        
        if not self.schedulers[s][ret.blockid].complete:
            complete = self.schedulers[s][ret.blockid].receive(encodedfragment, ret, peer)
            if complete:
                self.receiving.pop(ret.blockid)
                message = self.schedulers[s][ret.blockid].block
                self.checkRate(self.schedulers[s][ret.blockid])
                d = deferToThread(scanBlocks, message, peer)
                d.addCallback(self.triggerActions, message, peer)
        else:
            print 'received duplicate fragment ',ret.blockid,ret.fragmentid
        self.breakCall()
    

    def checkRate(self,block):
        return
        if not block.retr:
            rtime=time.time()-block.receivedTime
            rate=(block.getLenBlockData()-1400)/(rtime*1000)
            lastftime=block.sendTime + block.getLenNBlockData()/(block.rate*1000.0)
            """
            print '-------------------------'
            print 'send time:',block.sendTime
            print 'send last fragment:',lastftime
            print 'pass time:',rtime
            print 'fragments:',block.nfragments
            print 'size:',(block.nfragments-1)*1400,block.getLenNBlockData()
            print 'send rate:',block.rate, block.getLenNBlockData()/(block.rate*1000.0)
            """
            if rate<0:
                return
            if block.nfragments>5:
                print 'send:',block.rate,' received ',rate,' fragments:',block.nfragments
            rtt=block.sendTime+rtime
            RTTMessage.send(rate,rtt,block.rate,lastftime,block.getLenBlockData(),block.block.blockid,block.peer,self.controlPipe)
            #block.peer.meanRecRate.append(rate)
            #block.peer.meanRecRate=block.peer.meanRecRate[-20:]
            #mean=0
            #for m in block.peer.meanRecRate:
            #   mean +=m
            #print 'mean receiving rate from ',block.peer,mean/len(block.peer.meanRecRate)
    
    def checkLost(self):
        t=time.time()
        for block,scheduler in self.receiving.items():
            try:
                b=self.schedulers[scheduler][block]
            except:
                return
            if not b.retr and t-b.lastReceived>self.timeout:
                missed=[i for i in range(b.nfragments) if i not in b.fragments.keys()]
                for i in range(b.nfragments):
                    if i in b.fragments.keys():
                        break
                peer=b.fragments[i][2]
                b.retr=True
                print 'should request from ',peer,' to retransmist ',missed,' for block ',block
                scheduler.askFragments(block,missed,peer)
     
    """                               
    def expired(self, s, bid):
        if s not in self.schedulers:
            return
        if self.schedulers[s][bid].complete:
            return
        print 'expiredddddddddddd ',bid
        self.schedulers[s][bid].retr=True
        print self.schedulers[s][bid].fragments.keys()
        print self.schedulers[s][bid].nfragments
        print self.schedulers[s][bid].times
        print 'received:',self.schedulers[s][bid].receivedTime
        print 'timeout:',self.schedulers[s][bid].timeout
        print '1.5 timeout:',1.5*self.schedulers[s][bid].timeout
        print 'now:',time.time()
        missed=[i for i in range(self.schedulers[s][bid].nfragments) if i not in self.schedulers[s][bid].fragments.keys()]
        print 'missed:',missed
        for i in range(self.schedulers[s][bid].nfragments):
            if i in self.schedulers[s][bid].fragments.keys():
                break
        peer=self.schedulers[s][bid].fragments[i][2]
        print peer
        self.schedulers[s][bid].retransmited=True
        s.askFragments(bid,missed,peer)
        #del self.schedulers[s][bid]
    """
    
    def triggerActions(self, scannedblocks, message, peer):
        for b in scannedblocks:
            b.action(message, peer)
            
    def produceblock(self, r=None):
        '''
        remove this and make a new el for more sophisticated scheduler prio selection
        '''
        sl = self.schedulers.keys()
        if len(sl):
            s = choice(sl)
            reactor.callLater(0, s.produceBlock)
