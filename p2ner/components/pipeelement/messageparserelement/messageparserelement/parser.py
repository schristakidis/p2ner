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
        # if not scannedmsgs:
        #     try:
        #         print 'eeeeeeeeeeee:',self.parent.callSimple('getPort')
        #     except:
        #         print 'skataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'


    def encodingFailed(self,error,res,msg,data,peer):
        print 'encoding faileeddddddddddd'
        print error
        print res
        print msg
        print data
        print peer
