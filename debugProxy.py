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
from twisted.web.xmlrpc import Proxy,withRequest


class DebugProxy(xmlrpc.XMLRPC):
    def __init__(self,port=8881):
        xmlrpc.XMLRPC.__init__(self)
        print 'start listening xmlrpc'
        reactor.listenTCP(port, server.Site(self))


    @withRequest
    def xmlrpc_logError(self,request,message):
        print request.getClientIP(),message
        return True

if __name__=='__main__':
    DebugProxy()
    reactor.run()
