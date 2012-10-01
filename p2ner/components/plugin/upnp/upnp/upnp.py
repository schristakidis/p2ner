from mhelper import upnpUI
from twisted.internet import reactor
import util

class UPNP(object):
    
    def __init__(self,parent=False):
        self.upnp=False
        self.discovered=False
        self.log=parent.log
        self.parent=parent
        

        
    def startUpnp(self,ip,proto='UDP'):
        gateway=util.getGateway()
        if not gateway:
            self.log.error('UPNP could not find gateway')
            self.parent.upnpDiscoveryFailed()
        
        self.log.info('my gateway is %s',gateway)
        self.upnp=upnpUI(ip,gateway,proto)
        d=self.upnp.discover()
        d.addCallback(self.succesfulDiscovery)
        d.addErrback(self.failedDiscovery)
        
    def succesfulDiscovery(self,f):
        self.log.info('upnp device discovered')
        self.discovered=True
        self.parent.upnpDiscoverySuccesful()
        
    def failedDiscovery(self,f):
        self.log.error(f.getErrorMessage())
        self.parent.upnpDiscoveryFailed()
        
        
    def addPortMapping(self,port,exPort):
        if  not self.upnp:
            return

        if self.discovered:
            d=self.upnp.getSpecificPortMapping(port,exPort)
            if d[0]==0:
                self.portIsAllreadyForwarded(port,exPort)
            elif d[0]==1:
                self._addPortMapping(port,exPort)
            elif d[0]==2:
                 self.forwardFailed(port,exPort)
            elif d[0]==3:
                self.log.warning('port %s is forwarded for peer %s',str(exPort),str(d[1]))
                self.log.info('trying to forward ports %d,%d',port,exPort+2)
                self.addPortMapping(port, exPort+2)
            else:
                self.log.warning('port %s is forwarded to port %s',str(exPort),str(d[1]))
                self.log.info('trying to forward ports %d,%d',port,exPort+2)
                self.addPortMapping(port, exPort+2)
        else:
            reactor.callLater(1,self.addPortMapping,port,exPort)
            
    def _addPortMapping(self,port,exPort):
        d=self.upnp.addPortMapping(port,exPort)
        if d[0]:
            self.portIsForwarded(port,exPort)
        else:
            self.forwardFailed(port,exPort)
            
    def portIsAllreadyForwarded(self,port,exPort):
        self.log.warning('port %d is allready forwarded to %d',exPort,port)
        self.parent.portIsAllreadyForwarded(port,exPort)
        
        
    def portIsForwarded(self,port,exPort):
        #self.ports.append(port)
        self.log.info('port %d is forwarded to port %d',exPort,port)
        self.parent.portForwarded(port,exPort)
        
        
    def forwardFailed(self,port,exPort):
        self.log.error("port %d can't be forwarded to port %d",exPort,port)
        self.parent.forwardFailed(port,exPort)
        
    
    
if  __name__=='__main__':
    u=UPNP()
    ip=util.getIP()[0]
    u.startUpnp(ip)
    reactor.callLater(3,u.addPortMapping,50000,50001)
    reactor.callLater(6,u.addPortMapping,50004,50005)
    reactor.run()