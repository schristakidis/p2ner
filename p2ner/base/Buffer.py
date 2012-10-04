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


from bitarray import bitarray

class Buffer(object):

    def __init__(self, buffersize = 25,  buffer = bitarray(), lpb = 0, log=None):

        self.log=log
        self.lpb = lpb
        self.flpb = 0
        self.buffer = buffer
        if not buffer:
            if buffersize:
                self.buffer = bitarray('0'*buffersize)
        self.buffersize = len(self.buffer)

    def updateBlock(self, blockID, updateTo=True):
        '''
        Updates buffer any time a new block is received.
        startBuffer is always greater or equal to blockID.
        Otherwise the buffer can not be updated. (not always though...)
        '''
        index = self.lpb - blockID
        if index < 0 or index >= self.buffersize:
            print "Block id out of bounds of buffer.. id:%d lpb:%d buflen:%d D:%d" % (blockID,self.lpb,self.buffersize,index)
            return False
        else:
            self.buffer[index] = updateTo
            return True

    update = updateBlock

    def shift(self):
        '''
        Shifts all values of the list one position to the right.
        returns the ID of the popped block
        '''
        ret = self.lpb - self.buffersize
        self.lpb += 1
        playBlock=self.buffer.pop()
        if not playBlock:
            self.log.debug("missed block %d" %(self.lpb-1-self.buffersize))
        self.buffer.insert(0, False)
        if self.lpb - self.flpb > self.buffersize:
            return ret
        else :
            return -1
        
    def fillLevel(self):
        '''
        Get number of True blocks in buffer
        '''
        d = sum(self.buffer)
        return d

    def toBlockID(self, id):
        '''
        translate block number to block ID
        '''
        bid = self.lpb - id
        return bid
        
    def getTrueBIDList(self):
        '''
        get a list containing block IDs present in buffer
        '''
        buf = self.buffer
        l=[]
        for pos in range(self.buffersize):
            try:
                if buf[pos]:
                    l.append(self.toBlockID(pos))
            except:
                     print 'problem in buffer getTrueBiList!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                     print buf
                     print len(buf)
                     print pos
                     print self.buffersize
                     print l
                     continue
        return l
        """
        try:
            l = [self.toBlockID(pos) for pos in range(self.buffersize) if buf[pos]]
        except:
            print 'problem in buffer getTrueBiList!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print buf
            print self.buffersize
            print len(buf)
            l=[]
        return l
        """
        
    def getFalseBIDList(self):
        '''
        get a list containing block IDs not present in buffer
        '''
        l = [self.toBlockID(pos) for pos in range(self.buffersize) if not self.buffer[pos]]
        return l

    def bIDListCompTrue(self, obidlist):
        '''
        get the block IDs present in the given blockID list present in self
        '''
        bidlist = self.getTrueBIDList()
        l = [id for id in bidlist if id in obidlist]
        return l
    
    def getRelativeDeprivacy(self, obidlist):
        myFalses=self.getFalseBIDList()
        l = [id for id in myFalses if id in obidlist]
        l = [i for i in l if i>=self.flpb]
        return len(l)
    
    def __repr__(self):
        return "Buffer: '%s', lpb: %d" % (str(self.buffer), self.lpb)
    
if __name__ == "__main__":
    b = Buffer("peer",  10,  bitarray('1111000000'),  100)
    print b
    
    
