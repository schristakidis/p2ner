
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
Srate=700000/2 
START = threading.Event()
PeerRtt={}
LastAck=[]
GTsend=0
RTT1=0
RTT2=0

class XMLRPCserver(threading.Thread):

    def __init__(self, port=30000):
        threading.Thread.__init__(self)
        import xmlrpclib
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        
        def join(ip, port):
            global peers
            peers.append((ip, port),)
            PeerRtt[(ip,port)]={'min':None,'mean':None,'last':[],'congRtt':0}
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
	global GTsend,RTT1,RTT2
        threading.Thread.__init__(self)
        self.ack = ack
        self.bsize = bsize
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fragment = ""
        for i in xrange(fsize):
            self.fragment+=chr(random.randint(0,255))
        self.seq = 0
        self.Tsend = 0.1
        GTsend=self.Tsend
        history=4
        self.history_size=int(history/self.Tsend)
        self.not_ack = 0
        self.sum_idle = 0
        self.Window = 0
        self.umax = 1
        self.maxumax = 1
        self.u = 0
        self.f1 =2# 1.2
        self.f2 =1# 0.7
        self.f3 = 2
        self.idle=[]
        self.preUmax=0
        self.slowStart=True
        self.countPlot=0
        
    def run(self):
        global History, queue,AckHistory,RTT1,RTT2
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
            if time.time()-startTime<5:
                self.u=self.umax
            else:
                self.setUmax()
                self.setW()
                self.setU()
                self.countPlot +=1
                writer.writerow([self.countPlot,self.u,self.f1final,self.umax,self.maxumax,self.window,len(History),self.avRtt,self.rttRef,self.lrefRtt,RTT1,RTT2])
            if i == 0:
                try:
                    to, i = queue.get_nowait()
                    print to,i
                except:
                    print 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd'                   
            
            before = time.time()
            if not self.u:
                time.sleep(self.Tsend)
            for unow in range(self.u):
                if i == 0:
                    try:
                        to, i = queue.get_nowait()
                    except:
                         print 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'                        
                if i == 0:
                    self.idle[-1] +=1.0*self.Tsend/self.u
                    time.sleep(1.0*self.Tsend/self.u)
                    continue
                
                i -= 1
                self.seq+=1
                tosend = "".join([struct.pack("l", self.seq), self.fragment])
                #print 'sending to:',to 
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
        if self.umax>self.maxumax:
            self.maxumax=self.umax
        
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
        self.avRtt=0
        self.errorRtt=0
        self.minRtt=0
       
        
        Plock.acquire()
        sum2=0
        self.refRtt=0
        for k,v in sendPeers.items():
            self.refRtt +=v*PeerRtt[k]['ref']
            sum2 +=v
            
                   
        if self.refRtt:
            self.refRtt=self.refRtt/sum2
        else:
            self.refRtt=max([PeerRtt[k]['ref'] for k in PeerRtt.keys()])
            
        lastPeers={}
        lenPeers=len(LastAck)
        for p,r in LastAck:
            if not lastPeers.has_key(p):
                 lastPeers[p]={}
                 lastPeers[p]['count']=1
                 lastPeers[p]['rtt']=r
            else:
                lastPeers[p]['count'] +=1
                lastPeers[p]['rtt'] +=r
                
        self.rttRef=self.refRtt
        self.lrefRtt=0
        self.avRtt=0
        sum2=0
        for p,v in lastPeers.items():
            av=v['rtt']/v['count']
            ref=PeerRtt[p]['ref']
            self.lrefRtt += v['count']*(ref-av)
            self.avRtt +=v['rtt']
            sum2 +=v['count']
        Plock.release()
        self.avRtt=self.avRtt/sum2
	print 'average:',self.avRtt        
        if not self.lrefRtt:
            self.lrefRtt=self.refRtt  
            
        self.f1final=1
        
        #self.f1final=1+rttRef-self.avRtt
        #if self.f1final<1:
         #   self.f1final=1
        
     
	#print 'umax:',self.umax
	#print 'ref:',self.rttRef
	#print 'lref:',self.lrefRtt	
        self.window=(self.umax*(self.rttRef+self.Tsend)+(self.lrefRtt-self.avRtt)*self.umax*(self.rttRef+self.Tsend))
        try:
            self.window=ceil(self.winOld+0.3*(self.window-self.winOld))
        except:
            pass
        self.winOld=self.window
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
    
    def __init__(self, nreceivers=2):
        threading.Thread.__init__(self)
        self.nb = 7
        self.fperb=(Srate/self.nb)/1500
        self.sleep = 1.0/7
        self.nreceivers = nreceivers
        print self.fperb

    def run(self):
        global queue,peers
        START.wait()
        while True:
            
            newpeer=peers[:]            
            random.shuffle(newpeer)
            for i in range(min(self.nreceivers,len(peers))):
                    to = newpeer.pop()
                    queue.put_nowait((to, self.fperb))
            
            time.sleep(self.sleep)
            
                
            
class ACKreceiver(threading.Thread):
    
    def __init__(self, port=30000):
        threading.Thread.__init__(self)
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPdata.bind(("0.0.0.0", port))
	self.peers={}        
    def run(self):
        global History,LastAck,GTsend,RTT1,RTT2
        while True:
  
            data, addr = self.socketUDPdata.recvfrom(1024)
            now = time.time()
            seq=int(data)
            Hlock.acquire()
            AckHistory[-1]+=1
            tempAck=[]
            error=False
            for h in History:
                if h['s']<seq and h['to'][0]==addr[0]: 
                    tempAck.append(h)
                    error=True
                    print 'removing not acked block from history'
            History[:]=[h for h in History if h not in tempAck]
            for h in History:
                if h['s']==seq :
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
            if PeerRtt[peer]['congRtt']<rtt:
                  PeerRtt[peer]['congRtt']=rtt
            if error:
                if not PeerRtt[peer].has_key('meanmax'):
                    PeerRtt[peer]['meanmax']=[PeerRtt[peer]['last'][-1]] 
                    PeerRtt[peer]['meanmax'].append(rtt)
                else:
                    PeerRtt[peer]['meanmax'].append(PeerRtt[peer]['last'][-1])
                    PeerRtt[peer]['meanmax'].append(rtt)

                PeerRtt[peer]['meanmax']=PeerRtt[peer]['meanmax'][-10:]
                PeerRtt[peer]['max']=sum(PeerRtt[peer]['meanmax'])/len(PeerRtt[peer]['meanmax'])
            PeerRtt[peer]['last'].append(rtt)
            PeerRtt[peer]['last']=PeerRtt[peer]['last'][-5:]
            LastAck.append((peer,rtt))
            LastAck=LastAck[-5:]
            if not peer in self.peers.keys():
                self.peers[peer]={}
                
                if not RTT1:
                    self.peers[peer]['p']=1
                else:
                    self.peers[peer]['p']=2
            self.peers[peer]['av']=sum(PeerRtt[peer]['last'])/len(PeerRtt[peer]['last'])
            
            for p in self.peers.values():
                if p['p']==1:
                    RTT1=p['av']
                else:
                    RTT2=p['av']   
            minRtt=PeerRtt[peer]['min']
            if not PeerRtt[peer].has_key('meanmax'):
                er=minRtt+GTsend
            else:
                er=PeerRtt[peer]['max']
            PeerRtt[peer]['ref']=minRtt+3*(er-minRtt)/4
	    #print 'min:',minRtt
	    #print 'max:',er
            Plock.release()        
      
            
    
    
        

if __name__ == '__main__':

    XMLRPC = XMLRPCserver()
    UDPs = UDPsender()
    ACK = ACKreceiver()
    P=Producer()
    
    XMLRPC.start()
    UDPs.start()
    ACK.start()
    P.start()
