# -*- coding: utf-8 -*-

from constructs.messages import MSG_TYPES
from p2ner.base.ControlMessage import ControlMessage

def decodemsgs(binmsg, messagetypes, decoded=None):
    if decoded==None:
        decoded = {}
    for t in messagetypes:
        if t not in MSG_TYPES:
            #self.log.error('received message has unknown type:%d',t)
            raise TypeError
        if t not in decoded: 
            decoded[t] = MSG_TYPES[t].parse(binmsg)
    #print "decoded"
    #print decoded
    return decoded
    
def triggermsg(totrigger, triggers):
    triggered = []
    for msg in totrigger:
        if msg.trigger(triggers[msg.type]):
            triggered.append((msg, triggers[msg.type]))
    return triggered
    
def scanMessages(header, message):
    codefiltered = ControlMessage.codefilter(header.code)
    messagetypes = [msg.type for msg in codefiltered]
    decoded = decodemsgs(message, messagetypes)
    triggered = triggermsg(codefiltered, decoded)
    if not len(triggered):
        fallbackmsgs = ControlMessage.fallbackmsgs()
        messagetypes = [msg.type for msg in fallbackmsgs]
        decoded = decodemsgs(message, messagetypes, decoded)
        triggered = triggermsg(fallbackmsgs, decoded)
    return triggered
