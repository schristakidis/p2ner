# -*- coding: utf-8 -*-

from construct import *
from buffer import BufferAdapter,  BufferStruct
from peer import PeerAdapter,  PeerStruct

PeerBufferStruct = Struct("peerbuffer", 
        PeerAdapter(PeerStruct),
        BufferAdapter(BufferStruct), 
        )

