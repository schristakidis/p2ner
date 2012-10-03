# -*- coding: utf-8 -*-
   
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



