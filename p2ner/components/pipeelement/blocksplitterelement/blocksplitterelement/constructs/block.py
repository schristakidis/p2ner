# -*- coding: utf-8 -*-

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


# Container(blockid  = <UInt32>), block = <block data>)
BaseBlock = Struct("baseblock",
        UBInt16("streamid"), 
        UBInt32("blockid"),
        BaseBlockAdapter(BaseBlockStruct),
        )

# Container(blockid  = <UInt32>), fragmentid = <fragment number>, fragments = <total fragments in block>, block = <block data>)
BlockFragment = Struct("blockfragment",
        UBInt16("streamid"), 
        UBInt32("blockid"),
        UBInt8("fragmentid"),
        UBInt8("fragments"),
        BaseBlockAdapter(BaseBlockStruct),
        )

# Container(blockid  = <UInt32>), fragmentid = <fragment number>, fragments = <total fragments in block>, block = <block data>, md5 = <md5sum>)
MD5BlockFragment= Struct("md5block",
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
