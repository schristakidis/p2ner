# -*- coding: utf-8 -*-

from p2ner.abstract.pipeelement import PipeElement
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from constructs.messageheader import MessageHeader
from p2ner.base.Peer import Peer,findLocalPeer

class HeaderParserElement(PipeElement):

    def initElement(self, *args, **kwargs):
        self.log.info('HeaderParser loaded')
    
    def send(self, res, msg, data, peer):
        d = deferToThread(self.encodeheader, res, msg, data)
        return d
    
    def redir(self, res, message, recTime):
        peer,header = res
        todecode = message[MessageHeader.sizeof():]
        d = self.forwardprev("receive", todecode, peer, recTime)
        reactor.callLater(0, d.callback, header)
        self.breakCall()
    
    def receive(self, message, (host, port), recTime ,dataPort=False):
        d = deferToThread(self.parseheader, message, host,port,dataPort)
        d.addCallback(self.redir, message, recTime)
        return d
    
    def parseheader(self, message, host,port,dataPort):
        header = MessageHeader.parse(message)
        
        
        if dataPort:
            peer=findLocalPeer(host,dataPort=port)
        else:
            peer=findLocalPeer(host,port)
        

        if not peer:
            if header.port:
                port=header.port
 
            if not dataPort:
                peer = Peer(host, port)
            else:
                peer = Peer(host, dataPort=port)
  
        return peer,header
    
    def encodeheader(self, res, msg, data):
        #print data
        #print '----------------------'
        header = MessageHeader.build(data.header)
        try:
            ret = "".join([header, res])
        except:
            print 'problem in encodeheaderrrrr!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            print data.header
            print header
            print res
        return ret
        