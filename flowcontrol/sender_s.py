
import socket
import threading
import time 
import random
import struct
from Queue import Queue
from math import ceil

peers = []
History = []
queue = Queue()
AckHistory=[]
Hlock = threading.RLock()
Srate = 6000000
START = threading.Event()
PeerRtt={}
Plock = threading.RLock()

class XMLRPCserver(threading.Thread):

    def __init__(self, port=30000):
        threading.Thread.__init__(self)
        import xmlrpclib
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        
        def join(ip, port):
            global peers
            peers.append((ip, port),)
            Plock.acquire()
            PeerRtt[(ip,port)]={'min':None,'mean':None,'last':[]}
            Plock.release()
            print 'peerssssssssssss:',peers

        def start():
            print "start"
            START.set()
        
        self.server = SimpleXMLRPCServer(("", 8000), allow_none=True)
        print "Listening on port 8000..."
        self.server.register_function(join, "join")
        self.server.register_function(start, "start")

    def run(self):
        self.server.serve_forever()
        print 'XMLRPC is over!'
        
class UDPsender(threading.Thread):
    
    def __init__(self, fsize=1400, ack=10, bsize=10):
        threading.Thread.__init__(self)
        self.ack = ack
        self.bsize = bsize
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fragment = ""
        for i in xrange(fsize):
            self.fragment+=chr(random.randint(0,255))
        self.seq = 0
        self.Tsend = 0.1
        history=4
        self.history_size=int(history/self.Tsend)
        self.not_ack = 0
        self.sum_idle = 0
        self.window = 0
        self.min_window = 4
        self.umax = 1
        self.u = 0
        self.f1 = 1.2
        self.f2 = 0.7
        self.f3 = 2
        self.idle=[]

        
    def run(self):
        global History, queue,AckHistory
        START.wait()
        i = 0
        startTime=time.time()
        to = None
        while True:
            self.idle.append(0)
            if len(self.idle)>self.history_size:
                self.idle.pop(0)
            Hlock.acquire()
            AckHistory.append(0)
            if len(AckHistory)>self.history_size:
                AckHistory.pop(0)
                #print 'len ack histoty issssssssssss:',len(AckHistory)
            Hlock.release()
            if time.time()-startTime<1:
                self.u=self.umax
            else:
                self.setUmax()
                self.setW()
                self.setU()
            if i == 0:
                try:
                    to, i = queue.get_nowait()
                except:
                    pass
            
            before = time.time()
            for unow in range(self.u):
                if i == 0:
                    try:
                        to, i = queue.get_nowait()
                    except:
                        pass
                if i == 0:
                    self.idle[-1] +=1.0*self.Tsend/self.u
                    time.sleep(1.0*self.Tsend/self.u)
                    continue
                
                i -= 1
                self.seq+=1
                tosend = "".join([struct.pack("l", self.seq), self.fragment])
                
                self.socketUDPdata.sendto(tosend, to)
                #print "send", self.seq, to
                Hlock.acquire()
                t = time.time()
                History.append({"to": to, "s": self.seq, "t1": t, "t2": 0})
                Hlock.release()
                time.sleep(1.0*self.Tsend/self.u)
            #print time.time() - before, "should be", self.Tsend
             
    def setUmax(self):
        global History
        Hlock.acquire()
       
        asum=sum(AckHistory)
        Hlock.release()
        #print 'in umax ack is:',asum
        self.umax=1.0*asum/(self.Tsend*len(AckHistory))
        #print 'umax is:',self.umax
        
        tidle=sum(self.idle)
        print 'idle is:',tidle
        self.umax=self.umax*(1+tidle/(1.0*self.Tsend*len(AckHistory)))
        print 'final umax is:',self.umax
    
    def setW(self):
        sendPeers={}
        Hlock.acquire()
        hsum=len(History)
        print 'unack packets are:',hsum
        
        for h in History:
            if not sendPeers.has_key('to'):
                sendPeers['to']=0
            sendPeers['to']+=1
        #print 'in window unack ',sendPeers
        Hlock.release()
        prtt=0
        for k,v in sendPeers.items():
            Plock.acquire()
            r=PeerRtt[k]['min']
            Plock.release()
            if not r:
                print 'no min'
                r=0.05
            prtt +=1.0*v*r
        #print 'prtt:',prtt
        try:
            prtt=prtt/hsum
        except:
            print 'in except'
            prtt=prtt
        #print 'final prtt ',prtt
        if not prtt:
            Plock.acquire()
            for p in PeerRtt.values():
                prtt+=p['min']
            prtt=prtt/len(PeerRtt)
            Plock.release()
        print 'final final prtt:',prtt    
        self.window=ceil(self.umax*prtt*self.f1)
        if self.window < self.min_window:
            self.window = self.min_window
        
        print 'window is :',self.window
        
    def setU(self):
        Hlock.acquire()
        hsum=len(History)
        Hlock.release()
        print 'in u anack is:',hsum
        self.u=self.f2*(self.window-hsum)
        if self.u>self.f3*self.umax:
            self.u=self.f3*self.umax
        if self.u<0:
            self.u=0
        self.u=int(ceil(self.u))
        print 'uuuuuuuuuuuuuuuuuu :',self.u
        if self.u<=0:
            self.u=1
            #import sys
            #sys.exit()    
            
class Producer(threading.Thread):
    
    def __init__(self, nreceivers=1):
        threading.Thread.__init__(self)
        self.nb = 7
        self.sleep = 1.0/7
        self.nreceivers = nreceivers
        
    def run(self):
        global queue,peers
        START.wait()
        while True:
            
            queue.put_nowait((peers[0], self.nb))
            """
            if len(peers) >= self.nreceivers:
                newpeer = random.shuffle(peers[:])
                print 'newpeerrrr ',newpeer
                for i in range(self.nreceivers):
                    to = newpeer.pop()
                    queue.put_nowait((to, self.nb))
            """
            time.sleep(self.sleep)
                
                
            
class ACKreceiver(threading.Thread):
    
    def __init__(self, port=30000):
        threading.Thread.__init__(self)
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPdata.bind(("0.0.0.0", port))
        
    def run(self):
        while True:
            data, addr = self.socketUDPdata.recvfrom(1024)
            now = time.time()
            
            seq=int(data)
            Hlock.acquire()
            AckHistory[-1]+=1
            for h in History:
                if h['s']==seq:
                    block=h
                    History.remove(h)
                    break
            Hlock.release()
            peer=block['to']
            tsend=block['t1']
            rtt=now-tsend
            #print block
            #print 'rtttttttttttttttttttttttt:',rtt
            Plock.acquire()
            #print PeerRtt[peer]
            if not PeerRtt[peer]['min'] or PeerRtt[peer]['min']>rtt:
                PeerRtt[peer]['min']=rtt
                #print 'in if'
            PeerRtt[peer]['last'].append(rtt)
            PeerRtt[peer]['last']=PeerRtt[peer]['last'][-5:]
            Plock.release()
                    
            """
            try:
                (item for item in History if item["s"] == int(data)).next()["t2"] = now
            except:
                print "not in history:", int(data), addr
                print History
            """
            
            
            #print "ack", data, addr
            
            
    
    
        

if __name__ == '__main__':
    import os
    try:
        XMLRPC = XMLRPCserver()
        UDPs = UDPsender()
        ACK = ACKreceiver()
        P=Producer()
    
        XMLRPC.start()
        UDPs.start()
        ACK.start()
        P.start()
    except:
        os._exit()
