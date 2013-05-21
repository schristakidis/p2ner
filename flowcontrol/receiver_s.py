
import socket
import threading
import sys
import xmlrpclib
import struct
#import time
#from cPickle import dumps

IP = '192.168.1.2'
PORT = 30000

serverIP = '192.168.0.1'
serverXport = 8000
proxy = xmlrpclib.ServerProxy("http://%s:%d/" % (serverIP, serverXport), allow_none=True)

class UDPreceiver(object):
    
    def __init__(self, port=30001, ackport=30000):
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPack = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPdata.bind(("0.0.0.0", port))
        self.to = (serverIP, ackport)
        #self.receivedTime={}
        self.acked=0
        self.lastAcked=0
        
    def run(self):
        while True:
            data, addr = self.socketUDPdata.recvfrom(1500)
            #print len(data)
            
            try:
                seq = str(struct.unpack("l", data[0:4])[0])
                #self.receivedTime[seq]=time.time()
                #print 'received:',seq
            except:
                print data[0]
                print data[1:]
            
	    if int(seq)!=self.lastAcked+1:
		print 'missed packet'

            if seq>self.lastAcked:
                self.lastAcked=int(seq)
                
            self.socketUDPack.sendto(seq, self.to)
                
                
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
    UDP = UDPreceiver(PORT)
    proxy.join(IP, PORT)
    UDP.run()
