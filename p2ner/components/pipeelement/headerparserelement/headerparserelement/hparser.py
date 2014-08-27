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
from twisted.internet import reactor
from constructs.messageheader import MessageHeader,MessageHeaderIp,MessageHeaderSimple
from p2ner.base.Peer import Peer,findLocalPeer,findNatedPeer

class HeaderParserElement(PipeElement):

    def initElement(self, *args, **kwargs):
        self.log.info('HeaderParser loaded')

    def send(self, res, msg, data, peer):
        d = deferToThread(self.encodeheader, res, msg, data)
        return d

    def redir(self, res, message, recTime):
        peer,header = res
        if header.localIP:
            todecode = message[MessageHeaderIp.sizeof():]
        else:
            todecode = message[MessageHeaderSimple.sizeof():]
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
            try:
                lip=header.localIP
            except:
                lip=0

            if lip:
                if not dataPort:
                    peer = findNatedPeer(host,lip=lip,port=port)
                else:
                    peer = findNatedPeer(host,lip=lip, dataPort=port)

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
            self.breakCall()
        return ret

