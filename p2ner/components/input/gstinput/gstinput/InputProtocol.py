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
        # else:
        #    print "mes or err",data

    def getBuffer(self):
        buf=''
        j=len(self.buffer)
        for i in range(j):
            buf +=self.buffer.popleft()
        return buf

    def sendData(self,data):
        # print "sending data ",data
        self.transport.write(str(data))
        self.transport.write('\n')


    def closeInput(self):
        print 'closing inputtttttttttttttttttttttttt'
        try:
            self.transport.signalProcess('TERM')
        except:
            print 'proccess already exited'

    def processEnded(self,status):
        print 'process ended'
        # print status
