# -*- coding: utf-8 -*-

from construct import *



BlockHeader = Struct("header", 
        UBInt16("port"),
        )
