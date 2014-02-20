# -*- coding: utf-8 -*
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

from p2ner.abstract.ui import UI
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Site
from twisted.web.static import File
from twisted.internet import reactor
import re, os,sys
from pkg_resources import resource_string,resource_filename
current_dir = os.path.dirname(__file__)

class WebUI(UI):
    def initUI(self, serverport = 8880):
        r = P2Main(self)
        r.putChild('scripts',File(resource_filename(__name__, 'html')))
        self.listener=reactor.listenTCP(serverport, Site(r))
        self.log.info('WebServer listening on port %s...' % str(serverport))

    def stop(self):
        self.listener.stopListening()
        
class P2Main(Resource):
    isLeaf = False
    def __init__(self, parent):
        Resource.__init__(self)
        self.parent = parent
        ip=self.parent.root.netChecker.externalIp
        self.page=resource_string(__name__, 'html/index.html')%(ip,ip)

 
    def getChild(self, name, request):
        print name
        if name == '':
            return self
        return Resource.getChild(self, name, request)
 
    def render_GET(self, request):
        return self.page
