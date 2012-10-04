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