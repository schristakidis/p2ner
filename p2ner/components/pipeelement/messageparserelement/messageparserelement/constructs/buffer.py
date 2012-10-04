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


from construct import *
from p2ner.base.Buffer import Buffer
from bitarray import bitarray

class BitarrayAdapter(Adapter):
    def _encode(self, obj, ctx):
        return obj.tostring()
    def _decode(self,  obj,  ctx):
        r = bitarray()
        r.fromstring(obj)
        return r[:ctx.buffersize]

class BufferAdapter(Adapter):
    def _encode(self, obj, ctx):
        return Container(buffersize = obj.buffersize,  lpb = obj.lpb,  buffer = obj.buffer)
    def _decode(self,  obj,  ctx):
        return Buffer(buffersize = obj.buffersize,  lpb = obj.lpb,  buffer = obj.buffer)
    
BufferStruct = Struct( "buffer", 
                   UBInt8("buffersize"),
                   BitarrayAdapter(MetaField("buffer",  lambda ctx: -(-ctx["buffersize"]>>3))), 
                   UBInt32("lpb"), 
                   )

class RequestAdapter(Adapter):
    def _encode(self, obj, ctx):
        lpb = ctx["buffer"].lpb
        buffersize = ctx["buffer"].buffersize
        r = bitarray('0'*buffersize)
        for b in obj:
                r[lpb-b] = True
        return r.tostring()
    def _decode(self,  obj,  ctx):
        lpb = ctx["buffer"].lpb
        buffersize = ctx["buffer"].buffersize
        r = bitarray()
        r.fromstring(obj)
        ret = []
        for i in range(buffersize):
            if r[i]:
                ret.append(lpb-i)
        return ret
    
request = Optional(BitarrayAdapter(MetaField("request",  lambda ctx: -(-ctx["buffersize"]>>3)))), 

if __name__ == "__main__":
    q = Container(LPB = 6432, buffer = bitarray('0101100111'), buffersize=10, request=None)
    s = '\nY\xc0\x00\x00\x19 '
    parsed = BufferStruct.parse(s)
    built = BufferStruct.build(q)
    print "Check parsed == q"
    assert parsed == q
    print "OK"
    print "Check built == s"
    assert built == s
    print "OK"
    print "q=",  q
    print "built=   ",  repr(built)
    print "    s=   ",  repr(s)
    q = Container(LPB = 6432, buffer = bitarray('0101100111'), buffersize=10, request=bitarray('0101100111'))
    s = '\nY\xc0\x00\x00\x19 Y\xc0'
    parsed = BufferStruct.parse(s)
    built = BufferStruct.build(q)
    print "Check parsed == q"
    assert parsed == q
    print "OK"
    print "Check built == s"
    assert built == s
    print "OK"
    print "q=",  q
    print "built=   ",  repr(built)
    print "    s=   ",  repr(s)
