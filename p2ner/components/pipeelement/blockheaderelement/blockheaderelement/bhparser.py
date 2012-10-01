# -*- coding: utf-8 -*-

from p2ner.abstract.pipeelement import PipeElement
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from constructs.blockheader import BlockHeader
from p2ner.base.Peer import Peer,findLocalPeer
from construct import Container
import struct
import time

class BlockHeaderElement(PipeElement):

    def initElement(self, *args, **kwargs):
        self.log.info('BlockHeaderElement loaded')
    
    def send(self, res, msg, data, peer):
        d = deferToThread(self.encodeheader, res, msg, data,peer)
        return d
    
    def redir(self, bpeer, message, recTime):
        boolsize=struct.calcsize('!?')
        intsize=struct.calcsize('!H')
        doublesize=struct.calcsize('!d')
        peer=bpeer[0]
        bw=bpeer[1]
        sendTime=bpeer[2]
        todecode = message[boolsize+2*intsize+doublesize:]
        d = self.forwardprev("receive", peer,bw,recTime, sendTime)
        reactor.callLater(0, d.callback, todecode)
        self.breakCall()
    
    def receive(self, message, (host, port), recTime):
        d = deferToThread(self.parseheader, message, host,port,recTime)
        d.addCallback(self.redir, message, recTime)
        return d
    
    def parseheader(self, message, host,port,recTime):
        boolsize=struct.calcsize('!?')
        intsize=struct.calcsize('!H')
        doublesize=struct.calcsize('!d')
        normal=struct.unpack('!?',message[:boolsize])[0]
        if normal:
            mport = struct.unpack("!H", message[boolsize:boolsize+intsize])[0]
            peer=findLocalPeer(host,dataPort=port)
            if not peer:
                if int(mport)!=0:
                    peer = Peer(host, dataPort=mport)
                else:
                    peer = Peer(host, dataPort=port)
            bw = struct.unpack("!H", message[boolsize+intsize:boolsize+2*intsize])[0]
            t = struct.unpack("!d", message[boolsize+2*intsize:boolsize+2*intsize+doublesize])[0]
            return (peer,bw,t)
        else:
            todecode = message[boolsize:]
            hPipe=self._parent.holePuncher.holePipe.getElement(name="WrapperHeaderParserElement")
            hPipe.receive(todecode,(host, port), recTime)
            self.breakCall()
    
    def encodeheader(self, res, msg, data,peer):
        normal=struct.pack('!?',True)

        if not self._parent.pipePort:
            port=0
        else:
            port=self._parent.pipePort
        
        port = struct.pack('!H', port)
        try:    
            bw=int(peer.bw/1000)
            #print bw
            if int(peer.bw/1000)>65535:
                bw=65535
                #print int(peer.bw/1000)
        except:
            bw=1
        bw= struct.pack('!H',bw)
        t=struct.pack('!d',time.time())
        normal="".join([normal,port])
        port="".join([normal,bw])
        port=''.join([port,t])
        ret=[]
        for b in res:
            r = "".join([port, b])
            ret.append(r)
        return ret
        
