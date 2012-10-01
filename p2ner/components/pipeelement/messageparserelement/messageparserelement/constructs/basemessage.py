# -*- coding: utf-8 -*-

from construct import *
from cPickle import dumps, loads

BaseMessageStruct = Struct("message",
        UBInt16("length"),
        MetaField("message",  lambda ctx: ctx["length"]),
        )

class BaseMessageAdapter(Adapter):
        def _encode(self, obj, context):
            msg = dumps(obj, 2)
            return Container(message = msg,  length = len(msg))
        def _decode(self, obj, context):
            return loads(obj.message)
