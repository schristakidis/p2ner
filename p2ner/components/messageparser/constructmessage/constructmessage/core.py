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


from p2ner.abstract.messageparser import MessageParser
from twisted.internet.threads import deferToThread
from decodemessages import scanMessages
from encodemessages import encodemsg
from p2ner.base.ControlMessage import ControlMessage 

class ConstructMessageParser(MessageParser):
    
    def errback(self, failure): 
        self.log.error('failure in message construction %s',str(failure))
        return failure

    def initMessageparser(self, *args, **kwargs):
        self.log.info('ConstructMessage loaded')
    
    def encode(self, msg, content):
        d = deferToThread(encodemsg, msg, content)
        d.addErrback(self.errback)
        return d
    
    def decode(self, message, peer):
        #print "DECODE"
        d = deferToThread(scanMessages, message, peer)
        d.addCallback(self.triggerActions)
        d.addErrback(self.errback)
        
    def triggerActions(self, scannedmsgs):
        peer=scannedmsgs[1]
        scannedmsgs=scannedmsgs[0]
        for msg in scannedmsgs:
            msg[0].action(msg[1], peer)
            
if __name__ == "__main__":
    from time import time
    from construct import Container
    from p2ner.base.Consts import MessageCodes as MSG
    from p2ner.base.Buffer import Buffer
    from bitarray import bitarray
    from decodemessages import decodemsgs
    
    class MS(ControlMessage):
        type = "buffermessage"
        code = MSG.BUFFER
        ack = False
        
        def trigger(self, message):
            return True
        
        def action(self, message, peer):
            print message, peer
    
        
    oldnow = time()
    for i in xrange(100000):
        wheader = Container(header=Container(code=4, ack=False), streamid=111, buffer=Buffer(lpb=158, buffer=bitarray('00100010101010001010100101')), request=[150, 142, 140])
        decoded = Container(streamid=111, buffer=Buffer(lpb=158, buffer=bitarray('00100010101010001010100101')), request=[150, 142, 140])
        encoded = encodemsg(MS, decoded)
        if i==1:
            print wheader
            print decodemsgs(encoded, [MS.type])[MS.type]
        
    now = time()
    print now-oldnow
    
    class MS(ControlMessage):
        type = "sidmessage"
        code = MSG.BUFFER
        ack = False
        
        def trigger(self, message):
            return True
        
        def action(self, message, peer):
            print message, peer
            
    wheader = Container(header=Container(code=4, ack=False), streamid=111)
    decoded = Container(streamid=111)
    for i in xrange(100000):
        encoded = encodemsg(MS, decoded)
        if i==1:
            print wheader
            print decodemsgs(encoded, [MS.type])[MS.type]
        
    newnow = time()
    print newnow - now
    
