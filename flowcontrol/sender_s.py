
import socket
import threading
import time 
import random
import struct
from Queue import Queue
from math import ceil
import csv
csvfile = open('file.csv', 'wb')
writer = csv.writer(csvfile, delimiter=' ',quotechar='|', quoting=csv.QUOTE_MINIMAL)

peers = []
History = []
queue = Queue()
AckHistory=[]
Hlock = threading.RLock()
Plock = threading.RLock()
Srate = 6000000
START = threading.Event()
PeerRtt={}


class XMLRPCserver(threading.Thread):

    def __init__(self, port=30000):
        threading.Thread.__init__(self)
        import xmlrpclib
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        
        def join(ip, port):
            global peers
            peers.append((ip, port),)
            PeerRtt[(ip,port)]={'min':None,'mean':None,'last':[]}
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
        self.Window = 0
        self.umax = 1
        self.u = 0
        self.f1 =2# 1.2
        self.f2 =1# 0.7
        self.f3 = 2
        self.idle=[]
        self.preUmax=0
        self.slowStart=True

        
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
                print 'len ack histoty issssssssssss:',len(AckHistory)
            Hlock.release()
            if time.time()-startTime<1:
                self.u=self.umax
            else:
                self.setUmax()
                self.setW()
                self.setU()
                writer.writerow([self.u,self.f1,self.umax,self.window,len(History),self.avRtt,self.minRtt])
            if i == 0:
                try:
                    to, i = queue.get_nowait()
                except:
                    pass
            
            before = time.time()
            if not self.u:
                time.sleep(self.Tsend)
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
            print time.time() - before, "should be", self.Tsend
             
    def setUmax(self):
        global History
   
        Hlock.acquire()
       
        sum2=sum(AckHistory)
        Hlock.release()
        print 'in umax ack is:',sum2
        self.umax=1.0*sum2/(self.Tsend*len(AckHistory))
        print 'umax is:',self.umax
        
        tidle=sum(self.idle)
        print 'idle is:',tidle
        #self.umax=self.umax*(1+tidle/(1.0*self.Tsend*len(AckHistory)))
        self.umax=self.umax*self.Tsend*len(AckHistory)/(1.0*(self.Tsend*len(AckHistory)-tidle))
        print 'final umax is:',self.umax
    
    def setW(self):

        sendPeers={}
        Hlock.acquire()
        sum2=len(History)
        print 'unack packets are:',sum2
        for h in History:
            if not sendPeers.has_key(h['to']):
                sendPeers[h['to']]=0
            sendPeers[h['to']]+=1
        print 'in window unack ',sendPeers
        Hlock.release()
        prtt=0
        for k,v in sendPeers.items():
            Plock.acquire()
            r=PeerRtt[k]['min']
            try:
                av=sum(PeerRtt[k]['last'])/len(PeerRtt[k]['last'])
                self.avRtt=av
                self.minRtt=r
                self.f1=2-(av-r)/av
                print 'average:',av
                print 'min:',r
                print 'factor 11111:',self.f1
            except:
                print 'in except'
            Plock.release()
            if not r:
                print 'no min'
                r=0.05
            prtt +=v*r
        print 'prtt:',prtt
        try:
            prtt=prtt/sum2
        except:
            print 'in except'
            prtt=prtt
        print 'final prtt ',prtt
        if not prtt:
            Plock.acquire()
            for p in PeerRtt.values():
                prtt+=p['min']
            prtt=prtt/len(PeerRtt)
            Plock.release()
        print 'final final prtt:',prtt    
        prtt +=self.Tsend
        print 'prtt+Tsend:',prtt
        self.window=ceil(self.umax*prtt*self.f1)
        
        """
        if self.umax<self.preUmax:
			self.slowStart=False
        self.preUmax=self.umax
        
        if self.slowStart:
            try:
                self.window =2 *self.preWindow
            except:
                self.window *=2
            self.preWindow=self.window
            
        print 'slow start:',self.slowStart
        """
        print 'window is :',self.window
        
    def setU(self):

        Hlock.acquire()
        sum=len(History)
        Hlock.release()
        print 'in u anack is:',sum
        self.u=self.f2*(self.window-sum)
        if self.u>self.f3*self.umax:
            self.u=self.f3*self.umax
        if self.u<0:
            self.u=0
        self.u=int(ceil(self.u))
        print 'uuuuuuuuuuuuuuuuuu :',self.u
         
            
class Producer(threading.Thread):
    
    def __init__(self, nreceivers=1):
        threading.Thread.__init__(self)
        self.nb = 7
        self.fperb=(Srate/self.nb)/1500
        self.sleep = 1.0/7
        self.nreceivers = nreceivers
        
    def run(self):
        global queue,peers
        START.wait()
        while True:
            
            queue.put_nowait((peers[0], self.fperb))
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
        global History
        while True:
  
            data, addr = self.socketUDPdata.recvfrom(1024)
            now = time.time()
            
            seq=int(data)
            Hlock.acquire()
            AckHistory[-1]+=1
            tempAck=[]
            for h in History:
                if h['s']<seq:
                    tempAck.append(h)
                    print 'removing not acked block from history'
            History[:]=[h for h in History if h not in tempAck]
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
            #print PeerRtt[peer]
            Plock.acquire()
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

    XMLRPC = XMLRPCserver()
    UDPs = UDPsender()
    ACK = ACKreceiver()
    P=Producer()
    
    XMLRPC.start()
    UDPs.start()
    ACK.start()
    P.start()
