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
