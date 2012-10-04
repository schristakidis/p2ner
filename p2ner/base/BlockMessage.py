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
        