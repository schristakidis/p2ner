# -*- coding: utf-8 -*-

from construct import Container
from constructs.messages import MSG_TYPES

def encodemsg(msg, content):
    if msg.type not in MSG_TYPES:
        print msg.type, "not in",  MSG_TYPES

    #content.header=Container(code=msg.code, ack=msg.ack) #why again?

    try:
        encoded = MSG_TYPES[msg.type].build(content)
    except:
        print MSG_TYPES[msg.type].build(content)

    return encoded