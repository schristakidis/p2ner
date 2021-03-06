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
from twisted.internet import reactor, defer
from p2ner.base.Consts import MessageCodes as MSG
from p2ner.base.ControlMessage import MessageSent, MessageError
from construct import Container
from random import uniform
from time import time

class AckElement(PipeElement):

    def initElement(self, retries=5, timeout=0.5, dupeTimeout=10, **kargs):
        self.seq = 0
        self.timeout = timeout
        self.dupeTimeout = dupeTimeout
        self.retries = retries
        self.cache = {}
        self.log.info('AckElement loaded')
        self.acked = []

    def send(self, res, msg, data, peer):
        if getattr(msg, "ack", False):
            cdata = data.copy()
            cdata.header = data.header.copy()
            try:
                peer.ackRtt[self.seq]=time()
            except:
                self.log.error('problem in send in ack module')
                self.log.error('peer:%s',peer)
                self.log.error('msg:%s',msg)
                self.log.error('data header:%s',cdata.header)
                self.log.error('seq:%s',self.seq)
                self.breakCall()
            d = defer.Deferred()
            cdata.header.seq = self.seq
            cdata.header.ack = True
            tosend = {'res':res, 'msg':msg, 'data':cdata, 'peer':peer, 'retries':self.retries, 'd':d}
            self.cache[self.seq] = tosend
            fwd = self.forwardnext("send", msg, cdata, peer)
            reactor.callLater(0, fwd.callback, res)
            reactor.callLater(uniform(0.3, self.timeout), self.checkAck, self.seq)
            self.seq += 1
            if self.seq > 65535:
                self.seq = 0
            """
            print '-----------------'
            print 'sent'
            print self.seq-1
            print self.cache[self.seq-1]
            print '-------------------'
            """
            return d
        return res


    def receive(self, header, message, peer, recTime):
        peer.lastMessageTime=time()
        if header.code == MSG.ACK:
            if header.seq in self.cache:
                """
                print '----------------------'
                print 'received ack for message'
                print header.seq
                print self.cache[header.seq]
                print '---------------------------'
                """
                d = self.cache[header.seq]['d']
                p = self.cache[header.seq]['peer']
                del(self.cache[header.seq])

                if peer.ackRtt.has_key(header.seq):
                    peer.lastRtt.append(time()-peer.ackRtt[header.seq])
                    peer.lastRtt=peer.lastRtt[-5:]
                    peer.ackRtt.pop(header.seq)
                    #print peer,peer.lastRtt

                d.errback(defer.failure.Failure(MessageSent(p)))
            else:
                self.log.error('ack %d not in cache',header.seq)
                self.log.error('header:%s',header)
                self.log.error('%s',self.cache)
            self.breakCall()
        elif header.ack:
            """
            print '--------------------------------'
            print 'rec message requaring ack'
            print peer
            print header.seq
            """
            dupe = (peer, header.seq)
            duplicate=False

            if dupe in self.acked:
                duplicate=True

            port=self._parent.controlPipe.getElement(name="UDPPortElement").port

            localIP=None
            lip=False
            try:
                nType=self.root.netChecker.natType
            except:
                nType=0
            if nType==3:
                localIP=self.root.netChecker.localIp
                lip=True

            ack = Container(header=Container(port=port, ack=False, seq=header.seq, code=MSG.ACK,lip=lip,localIP=localIP))
            d = self.forwardnext("send", None, ack, peer)
            reactor.callLater(0, d.callback, "")

            if duplicate:
                #print 'IT WAS A DUPLICATE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                self.breakCall()
            else:
                self.acked.append(dupe)
                reactor.callLater(self.dupeTimeout, self.acked.remove, dupe)
            #print '------------------------------------'
        return header


    def checkAck(self, seq):
        if seq in self.cache:
            tosend = self.cache[seq]
            tosend['retries'] -= 1
            if tosend['retries']:
                tosend['peer'].ackRtt[seq]=time()
                d = self.forwardnext("send", tosend['msg'], tosend['data'], tosend['peer'])
                reactor.callLater(0, d.callback, tosend['res'])
                reactor.callLater(self.timeout, self.checkAck, seq)
            else:
                self.log.warning("send failed:%s %s %s", seq,tosend['peer'],tosend['msg'])
                # print 'message ack failedddddddddddddddd'
                """
                print '--------------'
                print 'message sent failedddddddddddddddd'
                print seq
                print tosend
                print '------------------------'
                """
                d = tosend['d']
                del(self.cache[seq])
                if tosend['peer'].ackRtt.has_key(seq):
                    tosend['peer'].ackRtt.pop(seq)

                d.errback(defer.failure.Failure(MessageError(tosend['peer'])))
                return None
        return True
