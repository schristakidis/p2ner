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

from gtkgui.interface.xml.xmlinterface import Interface
            
class ProxyInterface(Interface):

    def setProxy(self,proxy):
        self.proxy=DummyProxy(proxy)
        
    def setForwardPeer(self,peer):
        self.proxy.setPeer(peer)
        
        
class DummyProxy(object):
    def __init__(self,proxy):
        self.proxy=proxy
        
    def setPeer(self,peer):
        self.peer=peer
        
    def callRemote(self,*args):
        args=list(args)
        args.append(self.peer)
        d=self.proxy.callRemote('proxyCommand',*args)
        return d
    