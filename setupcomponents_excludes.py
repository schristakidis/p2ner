# -*- coding: utf-8 -*-
   
import p2ner
from sys import argv, executable
import os

if len(argv)<2:
    print "USAGE: " + executable + " " + argv[0] + " [setup command (install, develop...)]"
    exit(0)

from p2ner.core.components import _entry_points
cd =  os.path.dirname( os.path.realpath( __file__ ) )

def get_user_data_dir():
    dir = None

    # WINDOWS
    if os.name == "nt":
        # Try env APPDATA or USERPROFILE or HOMEDRIVE/HOMEPATH
        if "APPDATA" in os.environ:
            dir = os.environ["APPDATA"]

        if ((dir is None) or (not os.path.isdir(dir))) and ("USERPROFILE" in os.environ):
            dir = os.environ["USERPROFILE"]
            if os.path.isdir(os.path.join(dir, "Application Data")):
                dir = os.path.join(dir, "Application Data")

        if ((dir is None) or (not os.path.isdir(dir))) and ("HOMEDRIVE" in os.environ) and ("HOMEPATH" in os.environ):
            dir = os.environ["HOMEDRIVE"] + os.environ["HOMEPATH"]
            if os.path.isdir(os.path.join(dir, "Application Data")):
                dir = os.path.join(dir, "Application Data")

        if (dir is None) or (not os.path.isdir(dir)):
            dir = os.path.expanduser("~")

        # One windows, add vendor and app name
        #dir = os.path.join(dir, vendor, app)

    # Mac
    elif os.name == "mac": # ?? may not be entirely correct
        dir = os.path.expanduser("~")
        dir = os.path.join(dir, "Library", "Application Support")
        #dir = os.path.join(dir, vendor, app)

    # Unix/Linux/all others
    else:
        dir = os.path.expanduser("~")
        #dir = os.path.join(dir, "." + app)
        # Some applications include vendor
        # dir = os.path.join(dir, ".vendor", "app")

    return dir


COMPONENTS_DIR = os.path.join(cd, "p2ner", "components") 
HOME_DIR=os.path.join(get_user_data_dir(),'bin')

c=executable+' setup.py '+argv[1]
os.system(c)
for ct in _entry_points:
    d = os.path.join(COMPONENTS_DIR, ct)
    directories = [os.path.join(d, dirname) for dirname in os.listdir(d) if os.path.isdir(os.path.join(d,dirname)) and dirname[0]!="."]
    print directories
    for p in directories:
        cpath = os.path.join(d, p)
        c = "cd " + cpath + " && " + executable + " setup.py " + argv[1]  + ' -s  '+ HOME_DIR
        os.system(c)


