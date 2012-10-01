# -*- coding: utf-8 -*-

import os, sys
import logging
import time
import logging.handlers
from p2ner.util.utilities import get_user_data_dir
from interfaceHandler import interfaceHandler



levels = {
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
    "debug": logging.DEBUG
}

class Logger(object):
    
    def __init__(self,level='debug',name='p2ner'):
        self.log = logging.getLogger(name)
        name=name+'.'
        userdatadir = get_user_data_dir()
        if not os.path.isdir(userdatadir):
            os.mkdir(userdatadir)
        if not os.path.isdir(os.path.join(userdatadir, "log")):
            os.mkdir(os.path.join(userdatadir, "log"))
        self.dir= os.path.join(get_user_data_dir(), "log",name)
        self.setupLogger(level)
        
    def setupLogger(self,level="debug", filename=None, filemode="a"):

        if not filename:
            filename = self.dir+"log"
            
        if not level or level not in levels:
            level = "error"

        self.log.setLevel(levels[level])

        handler = logging.handlers.RotatingFileHandler(filename, backupCount=10)
        formatter = logging.Formatter("[%(levelname)-8s] %(name)s  %(asctime)s %(module)s(%(funcName)s):%(lineno)d %(message)s")
        handler.setFormatter(formatter)

        self.log.addHandler(handler)
        
        self.log.handlers[0].doRollover()
        
        self.log.debug('\n---------\nLog started on %s.\n---------\n' % time.asctime())

        """
        logging.basicConfig(
                 level=levels[level],
                 format="[%(levelname)-8s] %(name)s  %(asctime)s %(module)s(%(funcName)s):%(lineno)d %(message)s",
                 datefmt="%H:%M:%S",
                 filename=filename,
                 filemode=filemode
                 )
        """
    def setLoggerLevel(self,level): 
        if level not in levels:
            return
        self.log.setLevel(levels[level])

    def getLoggerChild(self,name,interface=None,level='debug'):
        try:
            log=self.log.getChild(name)
            if interface:
                self.add_handler(log,level,interfaceHandler(interface))
            return log
        except:
            return self.log

    def addFileHandler(self,name,level='debug'):
        if not level or level not in levels:
            level = "debug"
 
        log=self.getLoggerChild(name)
        filename=self.dir+(name+'.log')
        handler=logging.FileHandler(filename,mode='w')
        formatter = logging.Formatter("[%(levelname)-8s] %(name)s  %(asctime)s %(module)s(%(funcName)s):%(lineno)d %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(levels[level])
        log.addHandler(handler)
        
    def add_handler(self,log,level,handler):
        formatter = logging.Formatter("[%(levelname)-8s] %(name)s %(asctime)s %(module)s(%(funcName)s):%(lineno)d %(message)s")
        handler.setFormatter(formatter)
        if level not in levels:
            level='debug'
        handler.setLevel(levels[level])

        log.addHandler(handler)






        
        
        
