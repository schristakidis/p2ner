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

BaseBlockStruct = Struct("data",
        UBInt16("length"),
        MetaField("block",  lambda ctx: ctx["length"]),
        )

class BaseBlockAdapter(Adapter):
        def _encode(self, obj, context):
            return Container(block = obj,  length = len(obj))
        def _decode(self, obj, context):
            return obj.block

class RawBlock(object):
    
    @staticmethod
    def parse(message):
        return message
    
    @staticmethod
    def build(message):
        return message

MessageHeader = Struct("header", 
        UBInt16('port'),
        )


# Container(blockid  = <UInt32>), block = <block data>)
BaseBlock = Struct("baseblock",
        MessageHeader,
        UBInt16("streamid"), 
        UBInt32("blockid"),
        BaseBlockAdapter(BaseBlockStruct),
        )

# Container(blockid  = <UInt32>), fragmentid = <fragment number>, fragments = <total fragments in block>, block = <block data>)
BlockFragment = Struct("blockfragment",
        MessageHeader,
        UBInt16("streamid"), 
        UBInt32("blockid"),
        UBInt8("fragmentid"),
        UBInt8("fragments"),
        BaseBlockAdapter(BaseBlockStruct),
        )

# Container(blockid  = <UInt32>), fragmentid = <fragment number>, fragments = <total fragments in block>, block = <block data>, md5 = <md5sum>)
MD5BlockFragment= Struct("md5block",
        MessageHeader,
        UBInt16("streamid"), 
        UBInt32("blockid"),
        UBInt8("fragmentid"),
        UBInt8("fragments"),
        UBInt16("len"),
        BaseBlockAdapter(BaseBlockStruct),
        String("md5", 16),
        )

BLOCK_TYPES = {
             "rawblock": RawBlock,
             "baseblock" : BaseBlock,
             "blockfragment": BlockFragment,
             "md5blockfragment": MD5BlockFragment,
             }
