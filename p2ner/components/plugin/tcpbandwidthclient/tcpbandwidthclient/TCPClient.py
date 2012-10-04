
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
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.protocol import ClientCreator
import random



def BlockContent(blocksize = 1400):
    b = ""
    for i in xrange(blocksize):
        b+=chr(random.randint(0,255))
    return b

class TCPClient(Protocol):
    def __init__(self,parent):
        self.length = 0
        self.total = 1024*1024
        self.start = 0
        self.parent=parent
        
        
    def connectionMade(self):
        self.parent.printStatus('Connection made')
        self.sendChunk()
        
    def sendChunk(self):
        self.parent.printStatus('Started Measuring')
        chunk = BlockContent(self.total)
        self.transport.write(chunk)
        
    def dataReceived(self,data):
        self.parent.setBW(float(data)/1024)
        


        

class Client(object):
    def __init__(self,ip,gui,defer):
        self.gui=gui
        self.server=ip
        self.defer=defer
    
    def start(self):    
        creator = ClientCreator(reactor, TCPClient,self)
        d=creator.connectTCP(self.server, 60010)
        d.addErrback(self.failed)
        
    def failed(self,reason):
        if self.gui:
            self.gui.getResults(-1)
        if self.defer:
            self.defer.callback(-1)
            
    def printStatus(self,text):
        if self.gui:
            self.gui.addText(text)
            
    def setBW(self,bw):
        if self.gui:
            self.gui.getResults(bw)
        else:
            self.defer.callback(bw)