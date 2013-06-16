
import socket
import threading
import sys
import xmlrpclib
import struct
import csv
import time
#from cPickle import dumps

IP = '192.168.1.2'
PORT = 30000

serverIP = '192.168.0.1'
serverXport = 8000
proxy = xmlrpclib.ServerProxy("http://%s:%d/" % (serverIP, serverXport), allow_none=True)
cnt = 0
err = 0
clname = "client" + IP.split('.')[2]
csvfile = open(clname+".csv", 'wb')
writer = csv.writer(csvfile, delimiter=' ',quotechar='|', quoting=csv.QUOTE_MINIMAL)
cLock = threading.RLock()
START = threading.Event()

class UDPreceiver(threading.Thread):
    
    def __init__(self, port=30001, ackport=30000):
        threading.Thread.__init__(self)
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPack = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPdata.bind(("0.0.0.0", port))
        self.to = (serverIP, ackport)
        #self.receivedTime={}
        self.acked=0
        self.lastAcked=0
        self.notrunning = True
        
    def run(self):
        global cnt,err,START,cLock
        while True:
            data, addr = self.socketUDPdata.recvfrom(1500)
            #print len(data)
            cLock.acquire()
            try:
                seq = str(struct.unpack("l", data[0:4])[0])
                #self.receivedTime[seq]=time.time()
                cnt += 1
                if self.notrunning:
                  START.set()
                  self.notrunning = False
                print 'received:',seq
            except:
                print 'fail'
                #print data[0]
                #print data[1:]
            
	    if int(seq)!=self.lastAcked+1:
		print 'missed packet'
                err += int(seq)-self.lastAcked

            cLock.release()
            if seq>self.lastAcked:
                self.lastAcked=int(seq)
                
            self.socketUDPack.sendto(seq, self.to)
                
class Logger(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.time = 0
        

    def run(self):
        global err,cnt,cLock,START
        START.wait()
        while True:
          time.sleep(1)
          cLock.acquire()
          self.time += 1
          print "\n",cnt,err,"\n" 
          writer.writerow([self.time,cnt,err])
          cnt = 0
          err = 0
          cLock.release()
                   
         
if __name__ == '__main__':
    #port = 30000
    #while True:
    #    port+=1
    #    try:
    #        UDP = UDPreceiver(port)
    #        print port
    #        break
    #    except:
    #        pass
    lfile = Logger()
    lfile.setDaemon(True)
    UDP = UDPreceiver(PORT)
    UDP.setDaemon(True)
    proxy.join(IP, PORT)
    UDP.start()
    lfile.start()
    while True:
      time.sleep(100)
