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
