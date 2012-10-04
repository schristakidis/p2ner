from twisted.internet.protocol import Protocol, Factory
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
