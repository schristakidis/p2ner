# -*- coding: utf-8 -*-

from construct import *



MessageHeader = Struct("header", 
        Flag("ack"),
        UBInt8("code"),
        UBInt16('port'),
        )

MessageLongHeader = Struct("header", 
        Flag("ack"),
        UBInt8("code"),
        UBInt16("streamid"), 
        )
