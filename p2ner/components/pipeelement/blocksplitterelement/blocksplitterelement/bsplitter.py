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


from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from random import choice
from p2ner.abstract.pipeelement import PipeElement
from p2ner.base.Peer import Peer
from construct import Container
from constructs.block import BLOCK_TYPES


class Fragment(object):
    type = "blockfragment"


class BlockSplitterElement(PipeElement):

    def initElement(self, MTU=1400):
        self.MTU = MTU
        self.cache = {}
        self.log.info('BlockSplitterElement loaded')
        
    def inputblock(self, r, scheduler, bid, data):   
        sid = scheduler.stream.id        
        d = deferToThread(self.splitblock, sid, bid, data)
        return d
    
    def splitblock(self, sid, bid, data):
        ret = []
        f = self.split_len(data, self.MTU)
        flen = len(f)
        for i in range(flen):
            c=Container(streamid=sid, blockid=bid, data=f[i], fragmentid=i, fragments=flen)
            res = (self.encodefragment(Fragment,c ), c)
            ret.append(res)
        return ret
    
    def encodefragment(self, b, content):
        if b.type not in BLOCK_TYPES:
            raise
        encoded = BLOCK_TYPES[b.type].build(content)
        return encoded
    
    def decodefragment(self, b, data):
        if b.type not in BLOCK_TYPES:
            raise
        decoded = BLOCK_TYPES[b.type].parse(data)
        return decoded
        
    def split_len(self, seq, length):
        return [seq[i:i+length] for i in range(0, len(seq), length)]
        
