from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import time


class TCPReceiver(Protocol):
    def __init__(self):
        self.length = 0
        self.total = 1024*1024
        self.start = 0
        
    def connectionMade(self):
        print 'new connection'
        
    def dataReceived(self, data):
        if self.length == 0:
            self.start = time.time()
        l = len(data)
        self.length += l
        print "RECV: %s"%l, "  RATE: ", 1.0*self.length/(time.time()-self.start)
        if self.length==self.total:
            self.calculateRate()
                    
    def calculateRate(self):
        rate =  1.0*self.length/(time.time()-self.start)
        print "RATE:", rate
        self.transport.write(str(rate))
        self.transport.loseConnection()
        
        


class Server(object):
    def __init__(self):
        pass
    
    def startListening(self):    
        factory = Factory()
        factory.protocol = TCPReceiver
        a = reactor.listenTCP(60010, factory)
