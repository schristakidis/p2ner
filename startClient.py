# -*- coding: utf-8 -*-

from p2ner.base import *
import p2ner.abstract.engine
import subprocess
import p2ner.base.messages.bootstrap, twisted.application.internet, twisted.web.xmlrpc
from p2ner.core.components import getComponents, _entry_points, loadComponent
import weakref, twisted.internet, bitarray, construct
Client = loadComponent("engine", "ComboClient")
from twisted.internet import reactor
P2NER = Client(_parent=None,UI=('GtkGui',[],{}))
reactor.run()  
