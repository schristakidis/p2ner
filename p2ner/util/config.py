import os, sys
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

import ConfigParser
from p2ner.util.utilities import get_user_data_dir
from p2ner.core.components import getComponentsInterfaces,getComponentConfig
from hashlib import md5

config = None
configfile = None
chConfig=None
chConfigFile=None

def create_default_settings():
    global config
 
    for component in ('input','overlay','scheduler'):
        specs=getComponentsInterfaces(component)
        for comp,interface in specs.items():
            if not config.has_section(comp):
                config.add_section(comp)
            for k,v in interface.specs.items():
                config.set(comp,k,str(v))
                  
    
def create_default_config(filename):
    global config
    
    dir = os.path.dirname(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Standard configuration
    config = ConfigParser.ConfigParser()
    create_default_settings()
    
    config.add_section('Components')
    config.set('Components','input','VlcInput')
    config.set('Components','output','PureVlcOutput')
    config.set('Components','scheduler','PullClient')
    config.set('Components','overlay','CentralClient')

    config.add_section('ColumnVisibility')
    
    config.add_section('General')
    
    config.add_section('UPNP')
    config.set('UPNP','on','true')
    
    config.add_section('DefaultServ')
    config.set('DefaultServ', 'ip', '150.140.186.112')
    config.set('DefaultServ', 'port', '16000')
    
    config.add_section('Server0')
    config.set('Server0', 'ip', '150.140.186.112')
    config.set('Server0', 'port', '16000')
    config.set('Server0', 'valid', 'true')
    config.add_section('Server1')
    config.set('Server1', 'ip', '127.0.0.1')
    config.set('Server1', 'port', '16000')
    config.set('Server1', 'valid', 'true')

 
    # Writing configuration file
    with open(filename, 'wb') as configfile:
        config.write(configfile)
    
    #log.info("Default configuration file created in [%s]" % (filename))
        
    return config
        

def save_config():
    global config, configfile
    with open(configfile, 'wb') as cf:
        #log.info('Writing configuration file')
        config.write(cf)

    
def check_config():
    global config,configfile
    if not config:
        ret=init_config()
    return ret
"""
def check_chConfig():
    global chConfig,chConfigFile
    if not chConfig:
        init_config()
    return chConfigFile
"""    
def init_config(filename=None):
        global config, configfile,chConfig,chConfigFile
        if filename == None:
            dirname=get_user_data_dir()
            if not os.path.isdir(dirname):
                os.mkdir(dirname)
            
            chFilename=os.path.join(dirname, "chConfig.cfg")
            chConfigFile = chFilename
            if not os.path.exists(chFilename):
                ch=open(chFilename,'wb')
                ch.close()
                chConfig=ConfigParser.ConfigParser()
            
            filename = os.path.join(dirname, "config.cfg")
            if not os.path.exists(filename):
                create_default_config(filename)
                configfile = filename
                return (configfile,chConfigFile)
            
        chConfig = ConfigParser.ConfigParser()
        config = ConfigParser.ConfigParser()
        if config.read(filename) == []:
            print "Unable to load configuration file at [%s] or file not found" % (filename)
            raise ValueError(filename, 'Config file not found or unparsable')
        else:
            configfile = filename
            
        try:
            chConfig.read(chConfigFile)
        except:
            pass

        return (configfile,chConfigFile)

def create_remote_config(file,chfile,remote):
    global config, configfile, chConfig,chConfigFile
    dirname=get_user_data_dir()
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    if remote:
        name="rconfig.cfg"
        n='rChConfig.cfg'
    else:
        name="config.cfg"
        n='chConfig.cfg'
    filename = os.path.join(dirname, name)
    f=open(filename,'wb')
    for line in file:
        f.write(line)
    f.close()
    
    filename2 = os.path.join(dirname, n)
    f=open(filename2,'wb')
    if chfile!=-1:
        for line in chfile:
            f.write(line)
    f.close()
    
    config = ConfigParser.ConfigParser()
    if config.read(filename) == []:
        print "Unable to load configuration file at [%s] or file not found" % (filename)
        raise ValueError(filename, 'Config file not found or unparsable')
    else:
        configfile = filename
        
    chConfig=ConfigParser.ConfigParser()
    try:
        chConfig.read(filename2)
    except:
        pass
    
    chConfigFile=filename2 
    
    return (configfile,chConfigFile)
            
    
#return 0 after creating section if section not found, else return 1
def check_conf_section(comp,sect):
    global config
    specs=getComponentConfig(comp,sect)
    if not config.has_section(sect):
        config.add_section(sect)
        for k,v in specs.specs.items():
            config.set(sect,k,str(v))
        save_config()
        return 0
    else:
        change=False
        for k,v in specs.specs.items():
            if not config.has_option(sect,k):
                config.set(sect,k,str(v))
                change=True
            if change:
                save_config()
    return 1
    
def get_servers():
    global config
    if not config:
        init_config()
    sections = [i for i in config.sections() if 'Server' in i]
    servers = []
    for server in sections:
        new_server = {}
        new_server['ip'] = config.get(server, 'ip')
        new_server['port']=int(config.get(server, 'port'))
        new_server['valid'] = config.getboolean(server, 'valid')
        servers.append(new_server)
    return servers
        
def writeChanges(changes):
    global config
    
    sections = [i for i in config.sections() if 'Server' in i]
    for s in sections:
        config.remove_section(s)
        
    i=0
    for s in changes:
        sec='Server'+str(i)
        config.add_section(sec)
        config.set(sec,'ip',s[0])
        config.set(sec,'port',s[1])
        valid='false'
        if s[2]:
            valid='true'
        config.set(sec,'valid',valid)
        i+=1
    save_config()
    

    
def getVisibility(col):
    global config
    if not config:
        init_config()
        
    try:
        ret=config.getboolean('ColumnVisibility', col)
    except:
        config.set('ColumnVisibility', col, 'true')
        ret=True
        
    return ret

def saveVisibility(collumn):
    global config
    if not config:
        init_config()
    
    for col in column:
        if col[1]:
            value = 'true'
        else:
            value = 'false'
        config.set('ColumnVisibility', col[0], value)
    
    save_config()            
    
def get_channels():
    global chConfig
    if not chConfig:
        init_config()
        
        
    channels=chConfig.sections()
    if not channels:
        return {}
    ch={}
    for c in channels:
        ch[c]={}
        ch[c]['location']=chConfig.get(c,'location')
        ch[c]['program']=int(chConfig.get(c,'program'))
    return ch

def writeChannels(channels):
    global chConfig
    chConfig=ConfigParser.ConfigParser()
    for k,v in channels.items():
        if not chConfig.has_section(k):
            chConfig.add_section(k)
        chConfig.set(k,'location',v['location'])
        chConfig.set(k,'program',v['program'])
    save_chConfig()
    
def save_chConfig():
    global chConfig, chConfigFile
    with open(chConfigFile, 'wb') as cf:
        #log.info('Writing configuration file')
        chConfig.write(cf)

def getFirstRun():
    global config
    if not config:
        init_config()
    try:
        first=config.getboolean('boot', 'first')
        bw=config.get('boot','bw')
        prevIp=config.get('boot','previp')
        return first,float(bw),prevIp
    except:
        config.add_section('boot')
        config.set('boot','first','false')
        config.set('boot','bw','128')
        config.set('boot','previp','-1')
        return True,128,-1
        
def writeBW(bw,ip):
    global config
    config.set('boot','bw',bw)
    config.set('boot','previp',ip)
    save_config()

def getCheckNetMessages():
    global config
    try:
        check=config.getboolean('General', 'shownetmessages')
    except:
        config.set('General', 'shownetmessages',True)
        check=True
    return check

def setCheckNetAtStart(check):
    global config
    config.set('General', 'shownetmessages',check)
    save_config()
    
def getRemotePreferences():
    global config
    if not config:
        init_config()
    ret={}
    try:
        ret['enable']=config.getboolean('Remote','enable')
        ret['dir']=config.get('Remote','dir')
        ret['password']=config.get('Remote','password')
        return ret
    except:
        m=md5()
        m.update('')
        password=m.hexdigest()
        config.add_section('Remote')
        config.set('Remote','enable','false')
        config.set('Remote','dir','')
        config.set('Remote','password',password)
        return {'enable':False,'dir':'','password':password}
    
def setRemotePreferences(enable,dir,password):
        global config
        config.set('Remote','enable',enable)
        config.set('Remote','dir',dir)
        passwd=config.get('Remote','password')
        if passwd!=password:
            m=md5()
            m.update(password)
            password=m.hexdigest()
            config.set('Remote','password',password)
    