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


import weakref

def findPeer(ip, port=-1, dataPort=-1):
    '''
    returns peer(s) following the specified criteria
    '''
    if port == -1:
        l = [p for p in Peer._peerPool.values() if p.ip==ip]
        if dataPort is -1:
            return l

        p = [p for p in l if p.dataPort==dataPort]
        if len(p)==1:
            return p[0]

    p = Peer._peerPool.get((ip, port), None)

    return p

def findLocalPeer(ip, port=-1, dataPort=-1):
    '''
    returns peer(s) following the specified criteria
    '''
    l = [p for p in Peer._peerPool.values() if  p.lip==ip] #p.useLocalIp and
    if port == -1:
        l = [p for p in l if  p.ldataPort==dataPort]
        if l:
            return l[0]
    else:
        l = [p for p in l if  p.lport==port]
        if l:
            return l[0]

    return None

def findNatedPeer(ip,lip=None,port=None,dataPort=None):
    l = [p for p in Peer._peerPool.values() if p.ip==ip and p.lip==lip]
    if l:
        peer=l[0]
        if port:
            peer.natport=port
        else:
            peer.natdataPort=dataPort

        return peer

def getPeerList():
    '''
    returns the whole list of cached peers
    '''
    l = Peer._peerPool.values()
    return l

class Peer(object):
    '''
    Peer keep a dictionary of unique peer identities and contains
    peers basic parameters: ip, port, dataPort, latency and bandwidth
    a peer is identified by the tuple (ip, port) and other attributes
    can only be updated
    see
    http://www.suttoncourtenay.org.uk/duncan/accu/pythonpatterns.html#flyweight
    for information on how the class creation is handled
    '''
    _peerPool=weakref.WeakValueDictionary()

    def __new__(cls, ip, port=-1, dataPort=-1):
        ip = str(ip)
        port = int(port)
        dataPort = int(dataPort)
        obj = findPeer(ip, port, dataPort)
        if obj and obj.dataPort==0 and dataPort!=-1:
            obj.dataPort=dataPort

        if not obj:
            obj = object.__new__(cls)
            Peer._peerPool[(ip, port)] = obj
            obj.ip = ip
            obj.port = port
            obj.s = {}

            obj.nat=False

            obj.bw=0
            obj.reportedBW=0
            obj.rtt=0

            if dataPort != -1:
                obj.dataPort = dataPort
            else:
                obj.dataPort = 0

            obj.lip= None
            obj.lport=None
            obj.ldataPort=None
            obj.useLocalIp=False
            obj.hpunch=False
            obj.conOk=False
            obj.lastSend=0
            obj.portOk=False
            obj.dataPortOk=False
            obj.conProb=False
            obj.learnedFrom=None

            obj.participateSwap=False
            obj.ackRtt={}
            obj.lastRtt=[]
            obj.swapRtt=0
            obj.isNeighbour=False
            obj.askedReplace=False
            obj.natType=0
            obj.natport=None
            obj.natdataPort=None
        return obj


    def __init__(self, ip, port=-1, dataPort=-1):
        if dataPort != -1:
            self.dataPort = dataPort


    def serialize(self, fields):
        '''
        returns a tuple of values corresponding to the parameters
        in the tuple fields and False in place of non existing fields'
        values
        '''
        ret = []
        for f in fields:
            ret.append(getattr(self, f, False))

        ret = tuple(ret)
        return ret

    def __repr__(self):
        ret=" ".join(["Peer:",  ", ".join([str(self.ip), str(self.port),  str(self.dataPort), str(self.reportedBW)])])#,str(self.lastRtt),str(self.swapRtt) ])])
        if self.lip:
            ret=" ".join(["Peer:",  ", ".join([str(self.ip), str(self.port),  str(self.dataPort), str(self.lip), str(self.lport),  str(self.ldataPort), str(self.hpunch), str(self.natType) ])])
        if self.natType==3:
            ret=" ".join([ret,str(self.natport),str(self.natdataPort)])
        return ret

    def __getstate__(self):
        pickledict=self.__dict__.copy()
        try:
            pickledict.pop('checkResponse')
        except:
            pass
        return pickledict

    def getIP(self):
        return self.ip

    def getPort(self):
        return self.port

if __name__ == "__main__":
    a=Peer("127.0.0.1", 22, 23)
    print a
    print a.serialize(["ip", "port", "banana"])
    b = Peer("127.0.0.1", 22)
    assert b==a
