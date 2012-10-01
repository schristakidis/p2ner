# -*- coding: utf-8 -*-

from construct import *



MessageHeader = Struct("header", 
        UBInt16("port"),
        Flag("ack"),
        UBInt16("seq"),
        UBInt8("code"),
        )
