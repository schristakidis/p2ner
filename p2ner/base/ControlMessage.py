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


from p2ner.core.namespace import autoNS
from p2ner.abstract.message import Message
from weakref import ref

class MessageSent(Exception):
    def __init__(self, peer= None):
        self.peer = peer

class MessageError(Exception):
    def __init__(self, peer=None):
        self.peer = peer


def probe_ack(f,func=None,*args):
    f.trap(MessageSent,MessageError)
    if f.check(MessageSent):
        return True
    if f.check(MessageError):
        if func:
                func(peer=f.value.peer,*args)
        return False

def probe_rec(f,func=None,*args):
    f.trap(MessageSent,MessageError)
    if f.check(MessageSent):
        if func:
                func(peer=f.value.peer,*args)
        return False
    if f.check(MessageError):
        return True

def probe_all(f,suc_func=None,err_func=None,**kwargs):
    f.trap(MessageSent,MessageError)
    if f.check(MessageSent):
        if suc_func:
                suc_func(f.value.peer,**kwargs)
        return False
    if f.check(MessageError):
        if err_func:
                err_func(f.value.peer,**kwargs)
        return False


def trap_sent(f):
    f.trap(MessageSent,MessageError)


class ControlMessage(Message):
    __instances__ = []

    @property
    def code(self):
        return self.__class__.code

    @property
    def type(self):
        return self.__class__.type

    @property
    def ack(self):
        return self.__class__.ack

    @classmethod
    def _cleanref(cls, r):
        #print 'del',r
        #cls.Log().error('removing %s',str(r))
        ControlMessage.__instances__.remove(r)
        #print ControlMessage.__instances__

    @classmethod
    def remove_refs(cls,inst):
        #cls.Log.error('in remove refs')
        i=0
        for msg_ref in ControlMessage.__instances__:
            if msg_ref() is inst:
                found=i
                #cls.Log.debug('removing control message instance:%s',msg_ref())
                #cls.__instances__.remove(msg_ref)
                break
            i+=1
        ControlMessage.__instances__.pop(found)

    @autoNS
    def __init__(self, *args, **kwargs):
        ControlMessage.__instances__.append(ref(self, ControlMessage._cleanref))
        #if not  'Log' in ControlMessage.__dict__:
        #    ControlMessage.Log=ref(self.logger.getLoggerChild('messages',self.interface))
        #ControlMessage.Log().debug('registering message %s',str(self))
        self.initMessage(*args, **kwargs)


    def initMessage(self, *args, **kwargs):
        pass

    @classmethod
    def codefilter(cls, code):
        msglist = []
        for msg_ref in cls.__instances__:
            msg = msg_ref()
            if msg == None:
                continue
            if msg.type == "messageheader":
                continue
            elif msg.code == code or msg.code == "*":
                    msglist.append(msg)
        if len(msglist)==0:
            print "No matches for msg code", code
            #cls.Log.warning("No matches for msg code:%s", code)
            print "Message instances: ", [m() for m in cls.__instances__]
            #cls.Log.warning("Message instances:%s ",str( [m() for m in cls.__instances__]))
        return msglist

    @classmethod
    def fallbackmsgs(cls):
        msglist = []
        for msg_ref in cls.__instances__:
            msg = msg_ref()
            if msg:
                if msg.code == "-":
                    msglist.append(msg)
        return msglist

    @classmethod
    def trig(cls, msgs, triggers):
        triggered = []
        for msg in msgs:
            if msg.trigger(triggers[msg.type]):
                triggered.append((msg, triggers[msg.type]))
        return triggered

    def __str__(self):
        return "CODE: %d TYPE: %s ACK: %d" % (self.__class__.code, self.__class__.type, self.__class__.ack)

    def __repr__(self):
        return "%s()" % self.__class__.__name__

class BaseControlMessage(ControlMessage):

    @autoNS
    def __init__(self, *args, **kwargs):
        pass

    def trigger(self,message):
        pass

    def action(self,message,peer):
        pass
