# -*- coding: utf-8 -*-

from p2ner.abstract.message import Message
from p2ner.core.namespace import autoNS
from weakref import ref

class BlockMessage(Message):
    __instances__ = []
    
    @classmethod
    def clean_refs(cls):
        for msg_ref in cls.__instances__:
            if msg_ref() == None:
                cls.__instances__.remove(msg_ref)
    
    @autoNS
    def __init__(self, *args, **kwargs):
        BlockMessage.__instances__.append(ref(self))
        self.initMessage(*args, **kwargs)
        
    def initMessage(self):
        pass
        
        
    @classmethod
    def trig(cls, msgs, triggers):
        triggered = []
        for msg in msgs:
            if msg.trigger(triggers[msg.type]):
                triggered.append((msg, triggers[msg.type]))
        return triggered

    @classmethod
    def getInstances(cls):
        cls.clean_refs()
        return [msg() for msg in cls.__instances__]
        