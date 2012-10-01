# -*- coding: utf-8 -*-

from constructs.block import BLOCK_TYPES

def encodeblock(b, content):
    if b.type not in BLOCK_TYPES:
        raise
    encoded = BLOCK_TYPES[b.type].build(content)
    return encoded