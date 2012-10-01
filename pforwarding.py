import sys    
from optparse import OptionParser
from p2ner.core.components import loadComponent,getComponents
from twisted.internet import reactor        

def getIP():
    ip=[]
    if 'linux' in sys.platform:
        from socket import socket, SOCK_DGRAM, AF_INET
        s = socket(AF_INET, SOCK_DGRAM)    
        s.connect(('google.com', 0))
        ip=s.getsockname()
        s.close()
        if ip:
            ip=[ip[0]] 
    elif 'win' in sys.platform:
        import wmi
        c = wmi.WMI ()

        for interface in c.Win32_NetworkAdapterConfiguration (IPEnabled=1):    
            for ip_address in interface.IPAddress:
                print ip_address
                if '.' in ip_address and ip_address!='127.0.0.1' and ip_address!='0.0.0.0':
                    ip.append(ip_address)    
    else:
        print "operating system not supported"
        return False    
        
    if ip:
        return ip
    else:
        return False
    

class Upnp(object):
    def __init__(self):
        self.getOptions()
        self.ip=getIP()[0]
        self.logger=loadComponent('plugin', 'Logger')(name='upnp')
        self.log=self.logger.getLoggerChild('pforwarding')
        self.upnp=loadComponent('plugin','UPNP')(self)
        self.upnp.startUpnp(self.ip,self.proto)
        
    def getOptions(self):
        usage = "usage: %prog -p proto -i port -e port"
        parser=OptionParser(usage)
        parser.add_option('-p', dest='protocol', help='set the protocol UDP or TCP default=%default', metavar="PROTO", default='UDP')
        parser.add_option('-i', dest='inPort', help='the internal port', metavar='PORT', type='int')
        parser.add_option('-e', dest='exPort', help='the external port', metavar='PORT', type='int')
        (options, args) = parser.parse_args()
        
        if not options.protocol or not options.inPort or not options.exPort:
            parser.error('you should define all options')
        
        options.protocol=options.protocol.upper()
        if options.protocol!='UDP' and options.protocol!='TCP':
            print options.protocol
            parser.error('you should set as protocol UDP or TCP')
            
        self.proto=options.protocol
        self.inPort=options.inPort
        self.exPort=options.exPort
        
    def upnpDiscoverySuccesful(self):
        self.upnp.addPortMapping(self.inPort,self.exPort)
        
    def upnpDiscoveryFailed(self):
        print "couldn't discover upnp device"
        reactor.stop()
        
    def portIsAllreadyForwarded(self,port,exPort):
        print 'port is already forwarded'
        reactor.stop()
    
    def forwardFailed(self,port,exPort):
        print 'port forwarding failed'
        reactor.stop()
        
    def portForwarded(self,port,exPort):
        print 'external port ',exPort,' is succesfully forwarded to port ',port,' for protocol ',self.proto
        reactor.stop()

        
        
        
if __name__=='__main__':
    Upnp()
    reactor.run()
