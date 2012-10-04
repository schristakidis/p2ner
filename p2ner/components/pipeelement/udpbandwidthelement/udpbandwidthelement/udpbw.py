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
from p2ner.base.Peer import Peer
from collections import deque
import Queue
import socket
import threading
import time
import sys
import atexit

class SendingThread(threading.Thread):
    
    def __init__(self, parent, que, thres, alive):
        super(SendingThread, self).__init__()
        self.parent = parent
        self.alive = alive
        self.que = que
        self.thres = thres
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        if sys.platform == 'win32':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131071)
        
    def run(self):
        self.main()
            
    def main(self):
        while True:
            q = self.que.get()
            if q == None:
                return
            data, to, t = q
            self.socket.sendto(data, to)
            if self.que.qsize() ==0: #< self.thres:
                reactor.callFromThread(self.parent.askdata)
            time.sleep(t)

class BandwidthElement(PipeElement):

    def initElement(self, bw=150000, thres=3):
        self.log.info('BlockHeaderElement loaded')
        self.bw = bw
        self.que = Queue.Queue()
        self.thres = thres
        self.alive = [True]
        self.sending = SendingThread(self, self.que, thres, self.alive)
        self.sending.start()
        reactor.addSystemEventTrigger('before', 'shutdown', self.die)
        #atexit.register(self.die)
    
    def send(self, res, msg, data, peer):
        #CHECK IF PEER BW IS SET
        bw = getattr(peer, "bw", self.bw)
        #SET BW TO THE MIN
        bw = min(bw, self.bw)
        for r in res:
            nextiter=1.0*1400/bw#len(r)/bw
            #print nextiter,len(res),bw
            pack = (r, (peer.ip, peer.dataPort), nextiter)
            self.que.put(pack)
        self.breakCall()
        return res
    
    def askdata(self):
        d = self.forwardprev("produceblock")
        reactor.callLater(0, d.callback, "")
        
    def setbw(self, d, bw):
        self.bw = bw
        return bw
    
    def die(self):
        print "SendingThread"
        self.que.put(None)
        self.sending.join(0)
        
