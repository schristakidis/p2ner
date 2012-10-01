# -*- coding: utf-8 -*-

import p2ner.util.configuration
import p2ner.util.logger
from twisted.internet import reactor
from p2ner.util.logger import LOG as log
from namespace import Namespace, initNS

__all__ = ["start", "quit", "addResource"]

class _engine(Namespace):

    @initNS
    def __init__(self, presets, loglevel, confile):
        global P2NER
        if P2NER:
            print "Restarting engine"
        else:
            print "Starting engine"
        
        print "Setting up logger. Level: %s" % str(loglevel)
        p2ner.util.logger.setupLogger(loglevel)
        log.info('Logging')
        log.info("Loading configuration file: %s" % str(confile))
        print "Loading configuration file: %s" % str(confile)
        p2ner.util.configuration.init_config(confile)
        
        self.resources = {}

P2NER = _engine.__new__(_engine)

def start(presets = None, loglevel="debug", confile = None):
    global P2NER
    P2NER.__init__(presets, loglevel, confile)
    
def quit():
    reactor.stop()

def addResource(streamID, scheduler=None, overlay=None, control=None, traffic=None, outif=None, inif=None):
    global P2NER
    P2NER.streams[streamID] = StreamResource (streamID, scheduler, overlay, control, traffic, outif, inif)
    
def addPlugin():
    pass
