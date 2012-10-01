# -*- coding: utf-8 -*-

from p2ner.base.BlockMessage import BlockMessage
from constructs.block import BLOCK_TYPES,MessageHeader
from p2ner.base.Peer import Peer


def decodeblk(binblock, types, decoded=None):
    if decoded == None:
        decoded={}
    for t in types:
        if t not in BLOCK_TYPES:
            raise
        if t not in decoded: 
            decoded[t] = BLOCK_TYPES[t].parse(binblock)
    return decoded
    
def triggerblk(totrigger, triggers):
    triggered = []
    for b in totrigger:
        if b.trigger(triggers[b.type]):
            triggered.append((b, triggers[b.type]))
    return triggered
    
def scanBlocks(block,peer):
    header = MessageHeader.parse(block)
    dataPort=header.port
    peer=Peer(peer[0],dataPort=dataPort)
    instances = BlockMessage.getInstances()
    blocktypes = [b.type for b in instances]
    decoded = decodeblk(block, blocktypes)
    triggered = triggerblk(instances, decoded)
    return (triggered,peer)