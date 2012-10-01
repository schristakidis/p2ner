# -*- coding: utf-8 -*-

from p2ner.base import *
import p2ner.abstract.engine
import p2ner.base.messages.bootstrap, twisted.application.internet, twisted.web.xmlrpc
from p2ner.core.components import getComponents, _entry_points, loadComponent
import weakref, twisted.internet, bitarray, construct
Server = loadComponent("engine", "Server")
from twisted.internet import reactor
P2NER = Server(_parent=None, control = ("UDPCM", [], {"port":16000}),logger=('Logger',{'name':'p2nerServer'}),interface=('NullControl',[],{}))
reactor.run()