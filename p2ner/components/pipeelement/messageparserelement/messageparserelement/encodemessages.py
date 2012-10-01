# -*- coding: utf-8 -*-

from construct import Container
from constructs.messages import MSG_TYPES

def encodemsg(msg, content):
    if msg.type not in MSG_TYPES:
        raise

    try:
        encoded = MSG_TYPES[msg.type].build(content)
    except:
        import sys
        print sys.exc_info()[0]
        raise TypeError

    return encoded