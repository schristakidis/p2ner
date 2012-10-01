# -*- coding: utf-8 -*-

from p2ner.core.core import P2NER
from p2ner.util.logger import LOG as log
import time

statspluginclassname = "stats"

def counter(_name):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
                try:
                    stats.incrementKey(_name)
                except:
                    stats.addKey(_name, 1)
            return f(*args, **kwargs)
        return wrapped_f
    return wrap
    
def setValue(_name):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
                try:
                    stats.setKey(_name, ret)
                except:
                    stats.addKey(_name, ret)
            return ret
        return wrapped_f
    return wrap

def valuecounter(_name, _value):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
                if ret==_value:
                    try:
                        stats.incrementKey(_name)
                    except:
                        stats.addKey(_name, 1)
            return ret
        return wrapped_f
    return wrap

def neqvaluecounter(_name, _value):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
                if ret != _value:
                    try:
                        stats.incrementKey(_name)
                    except:
                        stats.addKey(_name, 1)
            return ret
        return wrapped_f
    return wrap

def incrementValuecounter(_name):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
                incr = ret
                try:
                    stats.incrementKey(_name, incr)
                except:
                    stats.addKey(_name, incr)
                #log.debug("%s: %d" % (_name, stats.getKey(_name)))
            return ret
        return wrapped_f
    return wrap

def ratio(_name, _up, _down):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
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
                #log.debug("%s: %d" % (_name, stats.getKey(_name)))
            return ret
        return wrapped_f
    return wrap
    
def timeratio(_name, _up):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if P2NER.plugins.hasPlugin(statspluginclassname):
                stats = P2NER.plugins.getPlugin(statspluginclassname)
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
            return ret
        return wrapped_f
    return wrap

def dumpStats():
    ret = {}
    if P2NER.plugins.hasPlugin(statspluginclassname):
        stats = P2NER.plugins.getPlugin(statspluginclassname)
        ret = stats.dumpKeys()
    return ret
