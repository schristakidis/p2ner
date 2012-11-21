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

from twisted.web import xmlrpc, server
from twisted.internet import reactor,defer
from cPickle import dumps,loads
from twisted.web.xmlrpc import Proxy


class VizirProxy(xmlrpc.XMLRPC):
    def __init__(self,vip,vport,port=9000):
        xmlrpc.XMLRPC.__init__(self)
        print 'start listening xmlrpc'
        reactor.listenTCP(port, server.Site(self))
        url="http://"+vip+':'+str(vport)+"/XMLRPC"
        self.proxy=Proxy(url)
        
        
    def xmlrpc_register(self,ip,rpcport,port,bw,server=False):
        print 'registered ',ip,port,bw
        self.proxy.callRemote('register',ip,rpcport,port,bw,server)
        return True
    
    def xmlrpc_getState(self):
        ret=[(dumps(k),dumps(v)) for k,v in self.peers.items()]
        return ret
        
    def xmlrpc_proxyCommand(self,*args):
        #cmd=args.pop(0)
        args=list(args)
        peer=args.pop(-1)
        url="http://"+peer[0]+':'+str(peer[1])+"/XMLRPC"
        proxy=Proxy(url)
        d=proxy.callRemote(*args)
        return d
    
def startVizirProxy():
    from twisted.internet import reactor
    import sys,getopt
    try:
        optlist,args=getopt.getopt(sys.argv[1:],'p:v:P:h',['port=','vizir=','vizirPort=','help'])
    except getopt.GetoptError as err:
        usage(err=err)
        
    port=9000
    vPort=9000
    vIP=None
    for opt,a in optlist:
        if opt in ('-p','--port'):
            port=int(a)
        elif opt in ('-v','--vizir'):
            vIP=a
        elif opt in ('-P','--vizirPort'):
            vPort=int(a)
        elif opt in ('-h','--help'):
            usage()
            
    if not vIP:
        usage(err='You must set the vizir ip to connect')
    
    VizirProxy(vIP,vPort,port)
    reactor.run()
    
def usage(err=None,daemon=False):
    import sys
    if err:
        print str(err)
    print ' -------------------------------------------------------------------------'
    print ' Run P2ner Vizir Proxy'
    print ' '
    print ' -p, --port port :define port'
    print ' -v, --vizir ip :the vizir ip to connect'
    print ' -P, --vizirPort port :the vizir  port to connect'
    print ' -h, --help :print help'
    print ' -------------------------------------------------------------------------'
    sys.exit(' ')
    
if __name__=='__main__':
    startVizirProxy()