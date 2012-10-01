# -*- coding: utf-8 -*-

from p2ner.core.core import P2NER
from p2ner.util.logger import LOG as log
import time

statspluginclassname = "stats"

def counter(caller, _name):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        try:
            stats.incrementKey(_name)
        except:
            stats.addKey(_name, 1)
    
def setValue(caller, _name, value):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        try:
            stats.setKey(_name, value)
        except:
            stats.addKey(_name, value)
    
def valuecounter(caller, _name, _value, ret):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        if ret==_value:
            try:
                stats.incrementKey(_name)
            except:
                stats.addKey(_name, 1)
    
def neqvaluecounter(caller, _name, _value, ret):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        if ret != _value:
            try:
                stats.incrementKey(_name)
            except:
                stats.addKey(_name, 1)

def incrementValuecounter(caller, _name, incr):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        try:
            stats.incrementKey(_name, incr)
        except:
            stats.addKey(_name, incr)
    
def ratio(caller, _name, _up, _down):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        if stats.hasKey(_down):
            d = stats.getKey(_down)
            n = 0
            if stats.hasKey(_up):
                n = stats.getKey(_up)
                r = float(n)/d
                try:
                    stats.setKey(_name, r)
                except:
                    stats.addKey(_name, r)
    
def timeratio(caller, _name, _up):
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        if hasattr(stats, 't0'):
            n = 0
            d = time.time() - stats.t0
            if stats.hasKey(_up):
                n = stats.getKey(_up)
                r = float(n)/d
                try:
                    stats.setKey(_name, r)
                except:
                    stats.addKey(_name, r)
    
def dumpStats(caller):
    ret = {}
    if "plugins" not in caller:
        return
    if statspluginclassname in caller.plugins:
        stats = caller.plugins[statspluginclassname]
        ret = stats.dumpKeys()
    return ret
