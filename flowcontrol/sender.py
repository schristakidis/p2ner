
import socket
import threading
import time 
import random
import struct
from Queue import Queue

peers = []
History = []
queue = Queue()
Hlock = threading.RLock()
Srate = 6000000
START = threading.Event()

class XMLRPCserver(threading.Thread):

    def __init__(self, port=30000):
        threading.Thread.__init__(self)
        import xmlrpclib
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        
        def join(ip, port):
            global peers
            peers.append((ip, port),)
            print peers

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
        self.history_size = 40
        self.not_ack = 0
        self.sum_idle = 0
        self.Window = 0
        self.umax = 1
        self.u = 0
        self.f1 = 1.2
        self.f2 = 0.7
        self.f3 = 2

        
    def run(self):
        global History, queue
        START.wait()
        i = 0
        to = None
        while True:
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
                    Hlock.acquire()
                    History.append({"idle": self.Tsend/self.u, "s": -1})
                    Hlock.release()
                    #print "idle"
                    time.sleep(1.0*self.Tsend/self.u)
                    continue
                
                i -= 1
                self.seq+=1
                ack = self.seq%self.ack == 0 or i == 0
                tosend = "".join([str(int(ack)), struct.pack("l", self.seq), self.fragment])
                
                self.socketUDPdata.sendto(tosend, to)
                print "send", self.seq, to
                Hlock.acquire()
                if ack:
                    t = time.time()
                    History.append({"to": to, "s": self.seq, "t1": t, "t2": 0})
                History = History[-self.history_size:]
                Hlock.release()
                time.sleep(1.0*self.Tsend/self.u)
            print time.time() - before, "should be", self.Tsend
             
    def setUmax(self):
        global History
        ##CALCULATE UMAX
        pass
    
    
    def setW(self):
        ##CALCULATE W
        self.Window = 10
        
    def setU(self):
        ##CALCULATE U
        self.u = 100
            
            
class Producer(threading.Thread):
    
    def __init__(self, nreceivers=1):
        threading.Thread.__init__(self)
        self.sleep = 1.0/7
        self.nb = 10
        self.nreceivers = nreceivers
        
    def run(self):
        global queue
        START.wait()
        while True:
            if len(peers) >= self.nreceivers:
                newpeer = random.shuffle(peers[:])
                for i in range(self.nreceivers):
                    to = newpeer.pop()
                    queue.put_nowait((to, self.nb))
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
            Hlock.acquire()
            try:
                (item for item in History if item["s"] == int(data)).next()["t2"] = now
            except:
                print "not in history:", int(data), addr
                print History
            Hlock.release()
            #print "ack", data, addr
            
            
    
    
        

if __name__ == '__main__':

    XMLRPC = XMLRPCserver()
    UDPs = UDPsender()
    ACK = ACKreceiver()
    
    XMLRPC.start()
    UDPs.start()
    ACK.start()
    
