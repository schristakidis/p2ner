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

from pkg_resources import iter_entry_points, working_set, Environment
import os, sys

_entry_points = {   
    "engine"        :   "p2ner.%s.engine",
    "stream"        :   "p2ner.%s.stream",
    "scheduler"     :   "p2ner.%s.scheduler",
    "producer"      :   "p2ner.%s.producer",
    "produceroverlay"      :   "p2ner.%s.produceroverlay",
    "overlay"       :   "p2ner.%s.overlay",
    "serveroverlay" :   "p2ner.%s.serveroverlay",
    "pipeelement"   :   "p2ner.%s.pipeelement",
    "ui"            :   "p2ner.%s.ui",
    'interface'     :   'p2ner.%s.interface',
    "input"         :   "p2ner.%s.input",
    "output"        :   "p2ner.%s.output",
    "plugin"        :   "p2ner.%s.plugin"
}

COMPONENTS_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
USER_COMPONENTS_DIR = ""
working_set.add_entry(COMPONENTS_DIR)
pkg_env = Environment([COMPONENTS_DIR])
for name in pkg_env:
    working_set.require(pkg_env[name][0].key)

sys.path.append(  COMPONENTS_DIR)  

def getComponents(ctype):
    ret = {}
    if ctype not in _entry_points:
        return ret
    for comp in iter_entry_points(group = _entry_points[ctype]%'components', name = None):
        ret[comp.name] = comp
    return ret

def getComponentsInterfaces(ctype):
    ret = {}
    if ctype not in _entry_points:
        return ret
    for comp in iter_entry_points(group = _entry_points[ctype]%'interface', name = None):
        ret[comp.name] = getComponentConfig(ctype,comp.name)
    return ret

def loadComponent(ctype, cname):
    ret = []
    if ctype not in _entry_points:
        print "CTYPE???"
        return ret
    for comp in iter_entry_points(group = _entry_points[ctype]%"components", name = cname):
        ret.append(comp)
    if len(ret) > 1:
        print ret
        print "Component conflict for entry point %s, name %s:\n%s" % (str(_entry_points[ctype])), (str(ret[0].name), str(ret))
        exit(0)
    if len(ret):
        ret = ret[0].load()
    else:
        ret = None
    return ret

def getComponentConfig(ctype, cname):
    ret = []
    if ctype not in _entry_points:
        print "CTYPE???"
        return ret
    for comp in iter_entry_points(group = _entry_points[ctype]%"interface", name = cname):
        ret.append(comp)
    if len(ret) > 1:
        print ret
        print "Component conflict for entry point %s, name %s:\n%s" % (str(_entry_points[ctype])), (str(ret[0].name), str(ret))
        exit(0)
    if len(ret):
        ret = ret[0].load()
    else:
        ret = None
    return ret
