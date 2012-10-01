# -*- coding: utf-8 -*-

from twisted.internet import protocol
from collections import deque
    

class InputProto(protocol.ProcessProtocol):
    def __init__(self):
        self.buffer=deque()

        
    def connectionMade(self):
        print "connecton made to new process"
  
    def childDataReceived(self,childFD, data):
        if  childFD==1:
            self.buffer.append(data)
        #else:
        #   print "mes or err",data

    def getBuffer(self):
        buf=''
        j=len(self.buffer)
        for i in range(j):
            buf +=self.buffer.popleft()
        return buf   
    
    def sendData(self,data):
        #print "sending data ",data
        self.transport.write(str(data))
        self.transport.write('\n')

        
    def closeInput(self):
        print 'closing inputtttttttttttttttttttttttt'
        self.transport.signalProcess('TERM')
        
    def processEnded(self,status):
        print 'in input protocolllllllllll'
        print status
