
import socket
import threading
import sys
import xmlrpclib
import struct

IP = sys.argv[1]
PORT = int(sys.argv[2])

serverIP = "127.0.0.1"
serverXport = 8000
proxy = xmlrpclib.ServerProxy("http://%s:%d/" % (serverIP, serverXport), allow_none=True)

class UDPreceiver(object):
    
    def __init__(self, port=30001, ackport=30000):
        self.socketUDPdata = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPack = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketUDPdata.bind(("0.0.0.0", port))
        self.to = (serverIP, ackport)
        
    def run(self):
        while True:
            data, addr = self.socketUDPdata.recvfrom(1500)
            #print len(data)
            if (int(data[0])):
                try:
                    seq = str(struct.unpack("l", data[1:9])[0])
                except:
                    print data[0]
                    print data[1:]
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
