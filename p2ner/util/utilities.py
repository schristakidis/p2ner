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

import sys,os,subprocess

def validIP(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    for item in parts:
        try:
            if not 0 <= int(item) <= 255:
                return False
        except:
            return False
    return True

def vlc_path():
    import ctypes
    # Used on win32 and MacOS in override.py
    plugin_path = None

    if sys.platform.startswith('linux'):
        return '/usr/bin/vlc'
        
    elif sys.platform.startswith('win'):
        import ctypes.util as u
        p = u.find_library('libvlc.dll')
        if p is None:
            try:  # some registry settings
                import _winreg as w  # leaner than win32api, win32con
                for r in w.HKEY_LOCAL_MACHINE, w.HKEY_CURRENT_USER:
                    try:
                        r = w.OpenKey(r, 'Software\\VideoLAN\\VLC')
                        plugin_path, _ = w.QueryValueEx(r, 'InstallDir')
    #                    log.info('VLC path: ' + plugin_path)
                        w.CloseKey(r)
                        break
                    except w.error:
                        pass
                del r, w
            except ImportError:  # no PyWin32
                pass
            if plugin_path is None:
                # try some standard locations.
                for p in ('Program Files\\VideoLan\\', 'VideoLan\\',
                          'Program Files\\',           ''):
                    p = 'C:\\' + p + 'VLC\\libvlc.dll'
                    if os.path.exists(p):
                        plugin_path = os.path.dirname(p)
                        break
            if plugin_path is not None:  # try loading
                p = os.getcwd()
                os.chdir(plugin_path)
                # if chdir failed, this will raise an exception
                dll = ctypes.CDLL('libvlc.dll')
                # restore cwd after dll has been loaded
                os.chdir(p)
            else:  # may fail
                try:
                    dll = ctypes.CDLL('libvlc.dll')
                except:
                    del p, u
                    return None
        else:
            plugin_path = os.path.dirname(p)
            dll = ctypes.CDLL(p)
        del p, u

    return plugin_path


import os, sys


def get_user_data_dir():
    app = "p2ner"
    vendor = "P2NER"
    dir = None

    # WINDOWS
    if sys.platform.startswith('win'):
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
       dir = os.path.join(dir, app)

    # Unix/Linux/all others
    else:
       dir = os.path.expanduser("~")
       dir = os.path.join(dir, "." + app)
       # Some applications include vendor
       # dir = os.path.join(dir, ".vendor", "app")

    return dir

def _dot2int(v):
    '''(INTERNAL) Convert 'i.i.i[.i]' str to int.
    '''
    t = [int(i) for i in v.split('.')]
    if len(t) == 3:
        t.append(0)
    elif len(t) != 4:
        raise ValueError('"i.i.i[.i]": %r' % (v,))
    if min(t) < 0 or max(t) > 255:
        raise ValueError('[0..255]: %r' % (v,))
    i = t.pop(0)
    while t:
        i = (i << 8) + t.pop(0)
    return i

def getVlcVersion():
    import vlc
    try:
        ver=vlc.libvlc_get_version()
        ver=ver.split()[0]
    except:
        ver='unknown'
    return ver

def getVlcHexVersion():
    if getVlcVersion()!='unknown':
        return _dot2int(getVlcVersion())
    else:
        return 0

def getVlcReqVersion():
    return '1.1.0'

def getVlcReqHexVersion():
    return _dot2int(getVlcReqVersion())

def getGateway():
    gateway=[]
    if 'linux' in sys.platform:
        route=subprocess.check_output(['/sbin/route','-n'])
        route=[r.split() for r in route.splitlines()]
        route=route[2:]
        gateway=[g[1] for g in route if 'G' in g[3]]
    elif 'win' in sys.platform:
        import wmi
        c = wmi.WMI ()
        
        for interface in c.Win32_NetworkAdapterConfiguration (IPEnabled=1):
            #print interface.Description, interface.MACAddress
            for ip_address in interface.DefaultIPGateway:
                gateway.append(ip_address)
    else:
        print "operating system not supported"
        return False
        
    if gateway:
        return gateway
    else:
        return False
            


def getIP(sip=None,sport=None):
    saddr=(sip,sport)
    if not sip:
        saddr=('google.com',0)
    ip=[]

    if 'linux' in sys.platform:
        """
        ifconf=subprocess.check_output('/sbin/ifconfig')
        f=ifconf.split('inet addr:')
        for line in f[1:]:
            line=line.split()
            if line[0]!='127.0.0.1':
                ip.append(line[0])
        """
        from socket import socket, SOCK_DGRAM, AF_INET
        s = socket(AF_INET, SOCK_DGRAM)    
        s.connect(saddr)
        ip=s.getsockname()
        s.close()
        if ip:
            ip=[ip[0]] 
    elif 'win' in sys.platform:
        import wmi
        c = wmi.WMI ()

        for interface in c.Win32_NetworkAdapterConfiguration (IPEnabled=1):    
            for ip_address in interface.IPAddress:
                print ip_address
                if '.' in ip_address and ip_address!='127.0.0.1' and ip_address!='0.0.0.0':
                    ip.append(ip_address)    
    else:
        print "operating system not supported"
        return False    
        
    if ip:
        return ip
    else:
        return False
    
def isLocalIP(ip):
    if ip.startswith('192.168.'):
        return True
    else:
        return False
    
def compareIP(previp):
    ip=getIP()
    ip=ip[0].split('.')[:-1]
    previp=previp.split('.')[:-1]
    return ip==previp
    
    
def findNextConsecutivePorts(port,IF=''):
    import socket
    while 1:
            try:
                sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
                sock1.bind((IF, port))
                sock2.bind((IF, port+1))
                sock1.close()
                sock2.close()
                break
            except socket.error:
                port=port+2
    return port

def findNextUDPPort(port,IF=''):
    import socket
    port=port+2
    while 1:
            try:
                sock1 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM, 0)
                sock1.bind((IF, port))
                sock1.close()
                break
            except socket.error:
                port=port+2
    return port

def findNextTCPPort(port,IF=''):
    import socket
    while 1:
            try:
                sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock1.bind((IF, port))
                sock1.close()
                break
            except socket.error:
                port=port+1
    return port
    