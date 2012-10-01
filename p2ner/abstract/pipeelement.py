# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from abc import abstractmethod
from twisted.internet import defer, reactor

class StopPipe(Exception):
    def __init__(self):
        pass

def errtrap(failure):
    failure.trap(StopPipe)
    
class PipeElement(Namespace):

    @initNS
    def __init__(self, *args, **kwargs):
        setattr(self, '__next', None)
        setattr(self, '__prev', None)
        if "name" in kwargs:
            self.name = kwargs.pop("name")
        else:
            self.name = self.__class__.__name__
        self.initElement(*args, **kwargs)
        
    @abstractmethod
    def initElement(self, *args, **kwargs):
        pass
    
    def breakCall(self):
        raise StopPipe

    def forwardnext(self, FUNC, *args, **kwargs):
        d = defer.Deferred()
        next = self.next
        while next:
            try:
                meth = getattr(next, FUNC, False)
            except:
                meth=False
            if callable(meth):
                d.addCallback(meth, *args, **kwargs)
            next = next.next
        d.addErrback(errtrap)
        return d
    
    def forwardprev(self, FUNC, *args, **kwargs):
        d = defer.Deferred()
        prev = self.prev
        while prev:
            try:
                meth = getattr(prev, FUNC, False)
            except:
                meth=False
            if callable(meth):
                d.addCallback(meth, *args, **kwargs)
            prev = prev.prev
        d.addErrback(errtrap)
        return d
        
    @property
    def next(self):
        ret = getattr(self, '__next')
        return ret
        
    @property
    def prev(self):
        ret = getattr(self, '__prev')
        return ret
    
    