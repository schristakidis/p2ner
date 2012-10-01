# -*- coding: utf-8 -*-

from p2ner.abstract.pipeelement import PipeElement
from twisted.internet import reactor

class MultiRecipientElement(PipeElement):
    
    def initElement(self):
        pass
    
    def send(self, res, msg, data, peer):
        if isinstance(peer, (list, tuple)):
            for p in peer:
                self.redir(res, msg, data, p)
            self.breakCall()
        return res
    
    def redir(self, res, msg, data, peer):
        d = self.forwardnext("send", msg, data, peer)
        reactor.callLater(0, d.callback, res)
