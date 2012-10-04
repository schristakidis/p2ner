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

   
import p2ner
from sys import argv, executable
import os

if len(argv)<2:
    print "USAGE: " + executable + " " + argv[0] + " [setup command (install, develop...)]"
    exit(0)

from p2ner.core.components import _entry_points
cd =  os.path.dirname( os.path.realpath( __file__ ) )

COMPONENTS_DIR = os.path.join(cd, "p2ner", "components") 
HOME_DIR=os.path.join(os.path.expanduser("~"),'bin')

scripts=False
c=executable+' setup.py'
if 'scripts' in argv:
    argv.remove('scripts')
    if '-s' not in argv:
        scripts=True
        
for s in argv[1:]:
    c=c+" "+s
os.system(c)
for ct in _entry_points:
    d = os.path.join(COMPONENTS_DIR, ct)
    directories = [os.path.join(d, dirname) for dirname in os.listdir(d) if os.path.isdir(os.path.join(d,dirname)) and dirname[0]!="."]
    print directories
    for p in directories:
        cpath = os.path.join(d, p)
        c = "cd " + cpath + " && " + executable + " setup.py " + argv[1] 
        if scripts:
           c=c+ ' -s  '+ HOME_DIR
        for s in argv[1:]:
            c=c+" "+s
        os.system(c)



