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
"""This module provides functions embeddable inside you components in order to collect statistics"""


import time

def setLPB(caller, lpb):
    """set the LPB
    
    This function sets the current LPB in the stats component, you should update it from the scheduler each time LPB changes in order to get consinstent stat values.
    
    :param caller: the calling Component (this is usually *self*)
    :param lpb: the current lpb
    :type caller: Namespace
    :type lpb: int
    :returns: nothing
    :rtype: None
    
    :Example:
    
    from p2ner.core.statsFunctions import setLPB
    setLPB(self, 231)
    
    """
    for s in caller.__stats__:
        s.setLPB(lpb)
    

def counter(caller, _name):
    """increment a counter
    
    This function creates a stats key if it doesn't exist yet, and increment it by 1 every time it's called.
    
    :param caller: the calling Component (this is usually *self*)
    :param _name: the key name
    :type caller: Namespace
    :type _name: string
    :returns: nothing
    :rtype: None
    
    :Example:
    
    from p2ner.core.statsFunctions import counter
    counter(self, "myCounter")
    
    """
    for s in caller.__stats__:
        try:
            s.incrementKey(_name)
        except:
            s.addKey(_name, 1)
    
def setValue(caller, _name, value):
    """set a stats key to a given value
       
    This function creates a stats key if it doesn't exist yet, and increment it by 1 every time it's called.
    
    :param caller: the calling Component (this is usually *self*)
    :param _name: the key name
    :param value: the key value
    :type caller: Namespace
    :type _name: string
    "type value: any
    :returns: nothing
    :rtype: None
    
    :Example:
    
    from p2ner.core.statsFunctions import setValue
    setValue(self, "myCounter", 244)
    
    """
    for s in caller.__stats__:
        try:
            s.setKey(_name, value)
        except:
            s.addKey(_name, value)
    
#def valuecounter(caller, _name, _value, ret):
#    """increment a counter
#    
#    This function creates and increment a counter every time it's called.
#    
#    :param caller: the calling Component (this is usually *self*)
#    :param _name: the counter name
#    :type caller: Namespace
#    :type lpb: string
#    :returns: nothing
#    :rtype: None
#    
#    :Example:
#   
#    from p2ner.core.statsFunctions import counter
#    counter(self, "myCounter")
#    
#    """
#    if caller.__stats__:
#        if ret==_value:
#            try:
#                caller.__stats__.incrementKey(_name)
#            except:
#                caller.__stats__.addKey(_name, 1)
#    
#def neqvaluecounter(caller, _name, _value, ret):
#    """increment a counter
#    
#    This function creates and increment a counter every time it's called.
#    
#    :param caller: the calling Component (this is usually *self*)
#    :param _name: the counter name
#    :type caller: Namespace
#    :type lpb: string
#    :returns: nothing
#    :rtype: None
#    
#    :Example:
#    
#    from p2ner.core.statsFunctions import counter
#    counter(self, "myCounter")
#    
#    """
#    if caller.__stats__:
#        if ret != _value:
#           try:
#                caller.__stats__.incrementKey(_name)
#            except:
#                caller.__stats__.addKey(_name, 1)

def incrementValuecounter(caller, _name, incr):
    """increment a counter by a given value
    
    This function creates and increment a counter by a given value every time it's called.
    
    :param caller: the calling Component (this is usually *self*)
    :param _name: the counter name
    :param incr: the increment value
    :type caller: Namespace
    :type _name: string
    :type incr: int
    :returns: nothing
    :rtype: None
    
    :Example:
    
    from p2ner.core.statsFunctions import incrementValuecounter
    incrementValuecounter(self, "myCounter", 23)
    
    """
    for s in caller.__stats__:
        try:
            s.incrementKey(_name, incr)
        except:
            s.addKey(_name, incr)
    
#def ratio(caller, _name, _up, _down):
#    """increment a counter
#    
#    This function creates and increment a counter every time it's called.
#    
#    :param caller: the calling Component (this is usually *self*)
#    :param _name: the counter name
#    :type caller: Namespace
#    :type lpb: string
#    :returns: nothing
#    :rtype: None
#    
#    :Example:
#    
#    from p2ner.core.statsFunctions import counter
#    counter(self, "myCounter")
#    
#    """
#    if caller.__stats__:
#        if caller.__stats__.hasKey(_down):
#            d = caller.__stats__.getKey(_down)
#            n = 0
#            if caller.__stats__.hasKey(_up):
#                n = caller.__stats__.getKey(_up)
#                r = float(n)/d
#                try:
#                    caller.__stats__.setKey(_name, r)
#                except:
#                    caller.__stats__.addKey(_name, r)
#    
#def timeratio(caller, _name, _up):
#    """increment a counter
#    
#    This function creates and increment a counter every time it's called.
#    
#    :param caller: the calling Component (this is usually *self*)
#    :param _name: the counter name
#    :type caller: Namespace
#    :type lpb: string
#    :returns: nothing
#    :rtype: None
#    
#    :Example:
#    
#    from p2ner.core.statsFunctions import counter
#    counter(self, "myCounter")
#    
#    """
#    if caller.__stats__:
#        if hasattr(caller.__stats__, 't0'):
#            n = 0
#            d = time.time() - caller.__stats__.t0
#            if caller.__stats__.hasKey(_up):
#                n = caller.__stats__.getKey(_up)
#                r = float(n)/d
#                try:
#                    caller.__stats__.setKey(_name, r)
#                except:
#                    caller.__stats__.addKey(_name, r)
    
def dumpStats(caller):
    """dumps the current stats dictionary
    
    This functions returns a copy of the stats dictionary with all stats key/values
    
    :param caller: the calling Component (this is usually *self*)
    :type caller: Namespace
    :returns: { 'key1':value1, 'key2':value2, ...}
    :rtype: dict
    :Example:
    
    from p2ner.core.statsFunctions import caller
    dumpStats()
    
    """
    ret = {}
    for s in caller.__stats__:
        ret = s.dumpKeys()
    return ret
