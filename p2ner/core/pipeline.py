# -*- coding: utf-8 -*

from p2ner.core.namespace import Namespace, initNS
from p2ner.abstract.pipeelement import StopPipe, errtrap
from p2ner.base.ControlMessage import ControlMessage
from weakref import ref
from random import random
from twisted.internet import defer, reactor
from construct import Container

class Pipeline(Namespace):

    @initNS
    def __init__(self, elements=[]):
        setattr(self, '__first', None)
        setattr(self, '__len', 0)
        self.pipePort=None
        for el in reversed(elements):
            self.insert(el)
            
    @property
    def len(self):
        ret = getattr(self, '__len')
        return ret

    def getPipeline(self):
        ret = []
        el = getattr(self, '__first')
        while el:
            ret.append(el.name)
            el = getattr(el, '__next')
        return ret

    def setPipePort(self,port):
        print 'setting pipe port to',port
        self.pipePort=port
        
    def insert(self, el):
        next = getattr(self, '__first')
        setattr(self, '__first', el)
        setattr(el, '__next', next)
        setattr(next, '__prev', el)
        setattr(self, '__len', self.len+1)
        
    def append(self, el):
        end = getattr(self, '__first')
        if not end:
            setattr(self, '__first', el)
            setattr(self, '__len', self.len+1)
            return
        else:
            while getattr(end, '__next'):
                end = getattr(end, '__next')
        setattr(end, '__next', el)
        setattr(el, '__prev', end)
        setattr(self, '__len', self.len+1)
    
    def insertAt(self, el, at):
        if at == 0:
            self.insert(el)
            return
        if at == self.len:
            self.append(el)
            return
        place = getattr(self, '__first')
        for i in range(at):
            place = place.next
        setattr(el, '__next', place)
        setattr(el, '__prev', place.prev)
        setattr(place, '__prev', el)
        setattr(el.prev, '__next', el)
        setattr(self, '__len', self.len+1)
        
    def removeElement(self, name=None, index=-1):
        if name:
            next = getattr(self, '__first')
            if next.name == name:
                setattr(self, '__first', getattr(next, '__next', None))
                if getattr(self, '__first'):
                    setattr(getattr(self, '__first'), '__prev', None)
                del(next)
                setattr(self, '__len', self.len-1)
                return
            while next:
                if name == next.name:
                    setattr(next.prev, '__next', next.next)
                    try:
                        setattr(next.next, '__prev', next.prev)
                    except:
                        pass
                    del(next)
                    setattr(self, '__len', self.len-1)
                    return
                next = getattr(next, '__next')
            raise IndexError
        elif int(index)>-1:
            place = getattr(self, '__first')
            if index==0:
                setattr(self, '__first', place.next)
                if getattr(self, '__first'):
                    setattr(getattr(self, '__first'), '__prev', None)
                del(place)
                setattr(self, '__len', self.len-1)
                return
            for i in range(index):
                place = place.next
            try:
                setattr(place.prev, '__next', place.next)
            except:
                pass
            try:
                setattr(place.next, '__prev', place.prev)
            except:
                pass
            del(place)
            setattr(self, '__len', self.len-1)
        else:
            raise IndexError
            
    def getElement(self, name=None, index=-1):
        if name:
            next = getattr(self, '__first')
            while next:
                if name == next.name:
                    return next
                next = getattr(next, '__next')
            raise IndexError
        elif int(index)>-1:
            place = getattr(self, '__first')
            for i in range(index):
                place = place.next
            return place
        else:
            raise IndexError
        
    def send(self, msg, content, peer):
        if issubclass(msg, ControlMessage):
            content.header = Container()
            content.header.code = msg.code
            content.header.ack = getattr(msg, 'ack', False)
            content.header.seq = 0
            port=self.root.controlPipe.getElement(name="UDPPortElement").port
            if self.pipePort:
                content.header.port = self.pipePort
            else:
                content.header.port = 0
            #print content
        d = self.call("send", msg, content, peer)
        return d
        
    def registerProducer(self, scheduler):
        d = self.call("registerScheduler", scheduler)
        return d
        
    def unregisterProducer(self, scheduler):
        d = self.call("unregisterScheduler", scheduler)
        return d
    
    def breakCall(self):
        raise StopPipe
        
    def call(self, FUNC, *args, **kwargs):
        el = getattr(self, '__first')
        d = defer.Deferred()
        res = None
        if 'res' in kwargs:
            res = kwargs.pop("res")
        while el:
            try:
                meth = getattr(el, FUNC, False)
            except:
                meth=False
            if callable(meth):
                d.addCallback(meth, *args, **kwargs)
            el = el.next
        d.addErrback(errtrap)
        if res:
            reactor.callLater(0, d.callback, res)
            return d
        reactor.callLater(0, d.callback, "")
        return d

    def printall(self):
        i=0
        next = getattr(self, '__first')
        while next:
            print i, getattr(next.prev, 'name', None),  next.name, getattr(next.next, 'name', None)
            next = next.next
            i+=1
        
if __name__ == "__main__":
    
    from p2ner.core.namespace import Namespace, initNS
    from twisted.internet import defer,reactor
    from p2ner.abstract.pipeelement import PipeElement, StopPipe

    R=Namespace()
    P=Pipeline()
    R.P = P


    class Banana(PipeElement):

        def initElement(self, *args, **kwargs):
            print "INIT BANANA"
    
        def chew(self, res, arg):
            print "chew BANANA"
            print "res", res, "arg", arg
            if arg==1:
                self.breakCall()
            return 'BANANA'
        
    class Melon(PipeElement):

        def initElement(self, *args, **kwargs):
            print "INIT MELON"
    
        def chew(self, res, arg):
            print "chew MELON"
            print "res", res, "arg", arg
            return 'MELON'
        
    class Apple(PipeElement):

        def initElement(self, *args, **kwargs):
            print "INIT APPLE"
    
        def chew(self, res, arg):
            print "chew APPLE"
            d = defer.Deferred()
            reactor.callLater(2, d.callback, "APPLE IS BACK")
            return d

    def mod(ret):
        ret = ret+"1"
        print "mod"
        return ret

    class Orange(PipeElement):
        
        def redir(self, ret):
            self.forwardprev("chew", 'REDIR')
            self.breakCall()

        def initElement(self, *args, **kwargs):
            print "INIT ORANGE"
    
        def chew(self, res, arg):
            print "chew ORANGE"
            d = defer.Deferred()
            d.addCallback(mod)
            d.addCallback(self.redir)
            d.addCallback(mod)

            reactor.callLater(2, d.callback, "ORANGE IS BACK")
            return d 
    
    class Peanut(PipeElement):

        def initElement(self, *args, **kwargs):
            print "INIT PEANUT"
    
        def chew(self, res, arg):
            print "chew PEANUT - this will except"
            res.addCallback(mod)
            return d 
        
    banana = Banana()
    apple = Apple()
    orange = Orange()
    peanut = Peanut()
    melon = Melon()
    R.P.append(orange)
    R.P.insert(apple)
    R.P.insertAt(banana, 1)
    #R.P.insertAt(peanut, 2)#THIS IS THE WRONG WAY TO MAKE AN ELEMENT
    R.P.insertAt(melon, 3)
    
    R.P.printall()
    #R.P.removeElement(name="Melon")
    #R.P.printall()
    #R.P.removeElement(index=1)
    #R.P.printall()
    #R.P.removeElement(index=0)
    #R.P.printall()
    #R.P.removeElement(index=1)
    #R.P.printall()
    #exit(0)
    #reactor.callLater(0, R.P.call, "chew", 1)
    reactor.callLater(0, R.P.call, "chew", 2)
    reactor.callLater(20, reactor.stop)
    reactor.run()

