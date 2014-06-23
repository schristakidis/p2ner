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

from p2ner.core.namespace import Namespace, initNS
import p2ner.util.utilities as util
from twisted.internet import reactor,defer
from p2ner.core.components import loadComponent
from p2ner.base.Peer import Peer
from p2ner.util.stun import get_ip_info
from twisted.internet.threads import deferToThread
from p2ner.util.utilities import findNextConsecutivePorts,findNextUDPPort
from twisted.internet.threads import deferToThread

class NetworkChecker(Namespace):
    @initNS
    def __init__(self,ip=None,port=None):
        self.secondRun=False
        self.nat=False
        self.hpunching=False
        self.upnp=False
        self.upnpDevice=None
        self.log=self.logger.getLoggerChild('network',interface=self.interface)
        self.log.debug('initting network checker')
        self.measureBW=True
        self.difnat=False
        self.natType=0
        self.getIP(ip,port)


    def getIP(self,ip,port):
        try:
            self.localIp=util.getIP(ip,port)[0]
        except:
            self.localIp=None
            self.log.warning('no local ip found')
            if not self.basic:
                self.networkUnreichable()

        self.log.info('local ip is %s',self.localIp)
        print 'ippppppppppppppppppp:',self.localIp

    def check(self):
        if not self.localIp and not self.basic:
            self.networkUnreichable()
        if not self.secondRun:
            self.controlPort=self.root.controlPipe.callSimple('getPort')
            self.dataPort=self.root.trafficPipe.callSimple('getPort')
        else:
            self.root.controlPipe.call('cleanUp')
            self.root.trafficPipe.call('cleanUp')
            self.log.warning('problem detected. Trying again for different ports')
            self.controlPort=findNextConsecutivePorts(self.controlPort+2)
            self.dataPort=self.controlPort+1
            # self.root.controlPipe.getElement(name="UDPPortElement").port=self.controlPort
            self.root.controlPipe.callSimple('setPort',self.controlPort)
            # self.root.trafficPipe.getElement(name="BoraElement").port=self.dataPort
            self.root.trafficPipe.callSimple('setPort',self.dataPort)

        self.nat=False
        self.hpunching=False
        self.upnp=False
        self.difnat=False

        if not self.root.basic:
            self.checkNet()
        else:
            self.defaultNetConfig()


    def checkNet(self):
        #self.controlPort=self.root.controlPipe.getElement(name="UDPPortElement").port
        print 'control port:',self.controlPort
        self.log.debug('local control port is %d',self.controlPort)
        self.log.debug('contacting stun server for control port')
        d=deferToThread(get_ip_info,'0.0.0.0',self.controlPort)
        d.addCallback(self._check)
        d.addErrback(self.stunFailed)

    def _check(self,ret):
        print ret
        self.type,self.externalIp,self.extControlPort=ret
        if self.type=='Blocked' or 'error' in self.type:
            self.stunFailed()
            return
        self.log.debug('external ip is %s',self.externalIp)
        self.log.debug('external control port is %d',self.extControlPort)
        self.log.debug('nat type is %s',self.type)
        #self.root.controlPipe.call('listen')

        #self.dataPort=self.root.trafficPipe.getElement(name="UDPPortElement").port

        if self.localIp==self.externalIp:
            print 'global internet:'
            self.extDataPort=self.dataPort
            self.log.debug('external data port is %d',self.extDataPort)
            self.log.debug('peer is not behind nat')
            #self.root.trafficPipe.call('listen')
            self.networkOk()
            return

        self.log.debug('local data port is %d',self.dataPort)
        reactor.callLater(0.2,self.checkDataPort)

    def checkDataPort(self):
        self.log.debug('contacting stun server for data port')
        d=deferToThread(get_ip_info,'0.0.0.0',self.dataPort)
        d.addCallback(self._checkDataPort)
        d.addErrback(self.stunFailed)
        return


    def _checkDataPort(self,ret):
        type,externalIp,self.extDataPort=ret
        if type=='Blocked'or 'error' in type:
            self.stunFailed()
            return
        self.log.debug('external data port is %d',self.extDataPort)
        self.log.debug('nat type is %s',type)
        print ret
        if type!=self.type:
            self.log.error("nat type doesn't match for control and data port")
            self.difnat=True

        #self.root.trafficPipe.call('listen')

        self.log.debug('peer is  behind nat')
        print 'peer is behind nat'
        self.nat=True
        if self.type=="Full Cone":
            self.hpunching=False
            self.natType=0
            self.networkOk()
            return
        reactor.callLater(0.1,self.checkUPNP)

    def stunFailed(self,error=None):
        if not self.secondRun:
            print 'errrrrror:',error
            self.secondRun=True
            self.check()
            return
        self.log.error('There was an error while contacting stun servers')
        self.log.error('Restart the application')
        self.networkUnreichable()

    def checkUPNP(self):
        self.log.info('trying upnp')

        valid=self.preferences.getUPNP()
        if not valid or self.upnpDevice:
            self.log.info('upnp is deactivated')
            self.checkStun()
            return

        self.upnpDevice=loadComponent('plugin',"miniUPNP")(self.controlPort,self.dataPort,self.log)
        d=deferToThread(self.upnpDevice.start)
        #d=self.upnpDevice.start()
        d.addCallback(self.upnpSuccess)
        d.addErrback(self.upnpFailed)

    def upnpFailed(self,reason):
        print 'upnpFailed'
        print reason.getErrorMessage()
        self.checkStun()

    def upnpSuccess(self,ports):
        print 'upnp successful'
        if ports[0]!=self.controlPort:
            self.controlPort=ports[0]
            self.root.controlPipe.call('cleanUp')
            self.log.warning('changing control port to  %s due to UPNP issues',self.controlPort)
            # self.root.controlPipe.getElement(name="UDPPortElement").port=self.controlPort
            self.root.controlPipe.callSimple('setPort',self.controlPort)
        if ports[1]!=self.dataPort:
            self.dataPort=ports[1]
            self.root.trafficPipe.call('cleanUp')
            self.log.warning('changing data port to  %s due to UPNP issues',self.dataPort)
            # self.root.trafficPipe.getElement(name="UDPPortElement").port=self.dataPort
            self.root.trafficPipe.callSimple('setPort',self.dataPort)

        self.upnp=True
        self.upnpControlPort=self.controlPort
        self.upnpDataPort=self.dataPort
        self.networkOk()


    def networkUnreichable(self):
        self.interface.networkStatus(False)
        print 'no network'
        self.log.error('there is a problem with network configuration')
        self.root.interface.networkUnreachable(False)

    def networkOk(self):
        self.root.controlPipe.call('listen')
        self.root.trafficPipe.call('listen')
        print 'network conditions are excellent'
        print 'external ipppppppppp:',self.externalIp
        print 'upnp:',self.upnp
        print 'nat:',self.nat
        print 'hole punching:',self.hpunching
        print 'type:',self.type
        if self.upnp:
            print 'upnp control:',self.upnpControlPort
            print 'upnp data:',self.upnpDataPort
            self.root.controlPipe.setPipePort(self.upnpControlPort)
            self.root.holePuncher.holePipe.setPipePort(self.upnpDataPort)
            self.root.trafficPipe.setPipePort(self.upnpDataPort)
        self.log.debug('network is ok')
        self.log.debug('external ip:%s',self.externalIp)
        self.log.debug('upnp:%s',self.upnp)
        self.log.debug('nat:%s',self.nat)
        self.log.debug('hole punching:%s',self.hpunching)
        if self.nat:
            self.log.debug('type:%s',self.type)
        self.getFirstRun()
        self.root.interface.networkStatus(True)
        return

    def defaultNetConfig(self):
        self.externalIp=self.localIp
        self.extControlPort=self.controlPort
        self.extDataPort=self.dataPort
        self.root.controlPipe.call('listen')
        self.root.trafficPipe.call('listen')
        self.getFirstRun()
        return

    def checkStun(self):
        print 'checking stun'
        if self.difnat:
            if not self.secondRun:
                self.secondRun=True
                self.check()
            else:
                self.networkUnreichable()
        elif self.type=="Full Cone":
            self.hpunching=False
            self.natType=0
            self.networkOk()
        elif 'Restric' in self.type and not 'Port' in self.type:
            self.natType=1
            self.hpunching=True
            self.networkOk()
        elif 'Port' in self.type:
            self.natType=2
            self.hpunching=True
            self.networkOk()
        elif 'Symmetric' in self.type:
            self.natType=3
            self.hpunching=True
            self.networkOk()
        else:
            if not self.secondRun:
                self.secondRun=True
                self.check()
            else:
                self.networkUnreichable()



    def getFirstRun(self):
        first,bw,previp=self.preferences.getFirstRun()
        if first:
            print 'first boot'
            self.root.setBW(300)
            self.measureBW=False #True
        else:
            if not previp==self.externalIp:
                print 'different location'
                self.root.setBW(300) #(bw)
                self.measureBW=False #True
            else:
                print 'same location'
                self.measureBW=False
                self.root.setBW(300) #(bw)
