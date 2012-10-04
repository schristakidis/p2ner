# -*- coding: utf-8 -*-
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


from p2ner.base import *
import p2ner.abstract.engine
import p2ner.base.messages.bootstrap, twisted.application.internet, twisted.web.xmlrpc
from p2ner.core.components import getComponents, _entry_points, loadComponent
import weakref, twisted.internet, bitarray, construct
Server = loadComponent("engine", "Server")
from twisted.internet import reactor
P2NER = Server(_parent=None, control = ("UDPCM", [], {"port":16000}),logger=('Logger',{'name':'p2nerServer'}),interface=('NullControl',[],{}))
reactor.run()