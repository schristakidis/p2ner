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

from twisted.internet import reactor,defer
from miniupnpc import UPnP
from p2ner.util.utilities import findNextUDPPort


class miniUPNP(object):
    def __init__(self,cport,dport,log=None):
        self.cport=cport
        self.dport=dport
        self.log=log
        
    
    def start(self):
        self.upnp=UPnP()
        self.upnp.discoverdelay=3000
        devices=self.upnp.discover()
        if not devices:
            reactor.callFromThread(self.log.error,'no upnp device found')
            raise ValueError('no devices found')
        f=self.upnp.selectigd()    
        reactor.callFromThread(self.log.info,'upnp device found')
        self.ip=self.upnp.lanaddr
        
        newcport=self.addPortMapping(self.cport)
        if newcport:
            newdport=self.addPortMapping(self.dport)
            if newdport:
                return (newcport,newdport) 
            else:
                raise ValueError('could not forward control port')
        else:
            raise ValueError('could not forward data port')


    def addPortMapping(self,port):
        reactor.callFromThread(self.log.info,'trying to forward port %d',port)
        pm=self.upnp.getspecificportmapping(port,'UDP')
        if pm:
            if self.ip==pm[0]:
                print 'port is already forwarded for this ip'
                reactor.callFromThread(self.log.info,'port %d is already forwarded for %s',port,self.ip)
                return port
            else:
                return self.addPortMapping(port=findNextUDPPort(port))
        try:    
            b = self.upnp.addportmapping(port, 'UDP', self.ip, port, 'P2NER', '')
        except:
            reactor.callFromThread(self.log.warning,'a problem occured trying to forward port %d',port)
            reactor.callFromThread(self.log.warning,'validating if port %d was correctly forwarded',port)
            self.upnp.discover()
            d=self.upnp.selectigd()
            pm=self.upnp.getspecificportmapping(port,'UDP')
            b=False
            if pm and self.ip in pm:
                b=True

        if b:
            reactor.callFromThread(self.log.info,'port %d was successfully forwarded',port)
            return port
        else:
            reactor.callFromThread(self.log.warning,"couldn't forward port %d",port)
            return False
        

