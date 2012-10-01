# -*- coding: utf-8 -*-

from p2ner.abstract.pipeelement import PipeElement
from twisted.internet.threads import deferToThread
from decodemessages import scanMessages
from encodemessages import encodemsg
from p2ner.base.ControlMessage import ControlMessage 
from construct import Container

class MessageParserElement(PipeElement):
    
    def errback(self, failure): 
        self.log.error('failure in message construction %s',str(failure))
        return failure

    def initElement(self, *args, **kwargs):
        self.log.info('ConstructMessage loaded')
    
    def send(self, res, msg, data, peer):
        d = deferToThread(encodemsg, msg, data)
        d.addErrback(self.encodingFailed,res,msg,data,peer)
        return d
    
    def receive(self, res, message, peer, recTime):
        d = deferToThread(scanMessages, res, message)
        d.addCallback(self.triggerActions, peer)
        return d
        
    def triggerActions(self, scannedmsgs, peer):
        for msg in scannedmsgs:
            msg[0].action(msg[1], peer)
            

    def encodingFailed(self,error,res,msg,data,peer):
        print 'encoding faileeddddddddddd'
        print error
        print res
        print msg
        print data
        print peer