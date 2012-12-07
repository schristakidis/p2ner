# -*- coding: utf-8 -*
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

import sys
from namespace import Namespace, initNS
from components import getComponentsInterfaces
import p2ner.util.config as config
from twisted.internet import reactor
from p2ner.util.utilities import get_user_data_dir

ENCODINGS={'Greek':'ISO-8859-7',
                      'Universal':'UTF-8',
                      'Western European':'Latin-9'}

class Preferences(Namespace):

    @initNS
    def __init__(self,remote=False,func=None):
        self.Init(remote,func)
    
    def Init(self,remote,func):
        self.components={}
        self.tempComponents={}
        self.remote=remote
        if func:
            self.func=func
        else:
            self.func=None
            
    def start(self):
        if not self.remote:
            self.filename,self.chFilename=config.check_config()
            self.getComponents()
        else:
            self.copyConfig()
            
    def copyConfig(self):
        reactor.callLater(0,self.interface.copyConfig)
        
    def getConfig(self,file):
        self.filename,self.chFilename=config.create_remote_config(file[0],file[1],True)
        self.getRemoteComponents()
        
    def getRemoteComponents(self):
        self.gotStats=False
        for comp in ['input','output','scheduler','overlay','stats']:
            reactor.callLater(0,self.interface.getComponentsInterfaces,comp)
    
    def setComponent(self,comp,interface):
        if comp=='stats':
            self.tempStatPrefs=interface
            self.gotStats=True
        else:
            self.tempComponents[comp]=interface
        for c in ['input','output','scheduler','overlay']:
            if c not in self.tempComponents.keys() or not self.gotStats:
                return
        self.constructPreferences()
        
    def getComponents(self):
        for comp in ['input','output','scheduler','overlay']:
            self.tempComponents[comp]=getComponentsInterfaces(comp)
        self.tempStatPrefs=getComponentsInterfaces('stats')
        self.constructPreferences()
        
    def constructPreferences(self):
        self.constructComponents()
        self.constructStats()
        self.getParameters()
        
    def constructComponents(self):
        """"
        component structure:
        1.keys components [input,output ....]
        2.components keys:
           default: the default component to use
           temp: the temp component to use
           subComp : dictionary
        3.subComp keys: the specific subcomponents
        4.subcomponents keys:
 
            value:the value of the parameter
            name:the name of the parameter for the Gui
            tooltip:
            default:the default value read from the subcomponent interface
            type:the type of the parameter
        
        self.components[Main Component]['subComp'][sub component][parameter]['value']
        """
        for comp,interface in self.tempComponents.items():       
            self.components[comp]={}
            self.components[comp]['default']=None
            self.components[comp]['subComp']={}
            for k,v in interface.items():
                try:
                    platform=v.platform
                except:
                    platform=None
                
                if not(not platform or platform in sys.platform):
                    break
                
                self.components[comp]['subComp'][k]={}
                
                if not config.config.has_section(k):
                    config.config.add_section(k)
                    
                for var,value in v.specs.items():
                    temp={}
                    try:
                        temp['value']=config.config.get(k,var)
                    except:
                        temp['value']=value
                        config.config.set(k,var,value)
                    temp['name']=v.specsGui[var]['name']
                    temp['tooltip']=v.specsGui[var]['tooltip']
                    temp['default']=value
                    temp['type']=type(value)
                    self.components[comp]['subComp'][k][var]=temp

            try:
                default=config.config.get('Components',comp)
                self.components[comp]['default']=default
            except:
                self.components[comp]['default']=None
                config.config.set('Components',comp,'')
            self.components[comp]['temp']=self.components[comp]['default']
        
        
    def constructStats(self):
        self.statsPrefs={}
        for stat,spec in self.tempStatPrefs.items():
            self.statsPrefs[stat]={}
            if not config.config.has_section('Statistics'):
                config.config.add_section('Statistics')
        
            try:
                enabled=config.config.getboolean('Statistics',stat)
            except:
                enabled=False
                config.config.set('Statistics',stat,'false')
                
            self.statsPrefs[stat]['enabled']=enabled
            self.statsPrefs[stat]['par']={}
            if not config.config.has_section(stat):
                config.config.add_section(stat)
                
            for var,value in spec.specs.items():
                self.statsPrefs[stat]['par'][var]={}
                try:
                    v=config.config.get(stat,var)
                    if v=='False':
                        v=False
                except:
                    v=value
                    config.config.set(stat,var,value)
                self.statsPrefs[stat]['par'][var]['value']=v
                self.statsPrefs[stat]['par'][var]['name']=spec.specsGui[var]['name']
                self.statsPrefs[stat]['par'][var]['tooltip']=spec.specsGui[var]['tooltip']
                self.statsPrefs[stat]['par'][var]['default']=v
                self.statsPrefs[stat]['par'][var]['type']=type(value)
                if spec.specsGui[var].has_key('type'):
                    self.statsPrefs[stat]['par'][var]['gtype']=spec.specsGui[var]['type']
     
    def getParameters(self):
        self.visibleCols={}
        
        self.showNetAtStart=config.getCheckNetMessages()
        
        try:
            self.convertedDir=config.config.get('General','cdir')
        except:
            dir=get_user_data_dir()
            self.convertedDir=dir
            config.config.set('General','cdir',dir)
            
        try:
            self.checkAtStart=config.config.getboolean('General','checkAtStart')
        except:
            self.checkAtStart=False
            config.config.set('General','checkAtStart','false')
            
        try:
            self.subEncoding=config.config.get('General','subsencoding')
        except:
            self.subEncoding='Greek'
            config.config.set('General','subsencoding','Greek')
            
        self.tempSubEncoding=self.subEncoding
        
        self.servers=config.get_servers()
        try:
            self.defaultServer=config.config.get('DefaultServ','ip')
        except:
            self.defaultServer=None
        
        try:
            self.upnp=config.config.getboolean('UPNP','on')
        except:
            self.upnp=True
            config.config.set('UPNP','on','true')
        
        self.remotePrefs=config.getRemotePreferences()
        
        self.channels=config.get_channels()
        
        if self.func:
            self.func()

    def save(self):
        config.writeChannels(self.channels)
        config.config.set('General','checkAtStart',self.checkAtStart)
        config.config.set('General','shownetmessages',self.showNetAtStart)
        config.config.set('General','cdir',self.convertedDir)
        config.config.set('General','subsencoding',self.subEncoding)
        
        config.config.set('DefaultServ','ip',self.defaultServer)
    
        config.writeChanges([(s['ip'],s['port'],s['valid']) for s in self.servers])
        
        config.config.set('UPNP','on',self.upnp)
        
        config.setRemotePreferences(self.remotePrefs['enable'],self.remotePrefs['dir'],self.remotePrefs['password'])
        
        self.saveSettings(save=False)
        
        for name,v in self.visibleCols.items():
            config.config.set('ColumnVisibility',name,v)
            
        for stat,v in self.statsPrefs.items():
            config.config.set('Statistics',stat,v['enabled'])
            for k in v['par'].keys():
                config.config.set(stat,k,self.statsPrefs[stat]['par'][k]['value'])

        config.save_config()
        if self.remote:
            self.saveRemoteConfig(False)
        

    def saveSettings(self,save=True):
        for comp in ['input','output','scheduler','overlay']:
            try:
                d=self.components[comp]['temp']
            except:
                d=self.components[comp]['default']
            config.config.set('Components',comp,d)
            for sub in self.components[comp]['subComp'].keys():
                for par,v in self.components[comp]['subComp'][sub].items():
                    config.config.set(sub,par,str(v['value']))
                    
        if save:
            config.save_config()
            
    def saveRemoteConfig(self,quit=True):
        f=open(self.filename,'rb')
        b=f.readlines()
        f.close()
        f=open(self.chFilename,'rb')
        r=f.readlines()
        f.close()
        self.interface.sendRemoteConfig(b,r,quit)
        
    ###VIEW FRAME
    def getCollumnVisibility(self,name):
        return config.getVisibility(name)
        
    def changeVisibility(self,col,vis):
        self.visibleCols[col]=vis
        
    ###GENERAL FRAME
    def getCheckNetAtStart(self):
        return self.showNetAtStart
    
    def setCheckNetAtStart(self,check,save=False):
        self.showNetAtStart=check
        if save:
            config.config.set('General','shownetmessages',self.showNetAtStart)
            config.save_config()
            
    def getCheckAtStart(self):
        return self.checkAtStart
    
    def setCheckAtStart(self,check):
        self.checkAtStart=check
        
    def getCDir(self):
        return self.convertedDir
    
    def setConvertedDir(self,filename):
        self.convertedDir=filename
    
    
    def getSubEncodings(self):
        ret={}
        ret['default']=self.tempSubEncoding
        ret['encodings']=ENCODINGS
        return ret
    
    def setTempSubEncoding(self,encoding):
        self.tempSubEncoding=encoding
        
    def setSubEncoding(self,encoding):
        self.tempSubEncoding=encoding
        self.subEncoding=encoding
        
    ###COMPONENT FRAME
    def setTempComponent(self,comp,temp):
        self.components[comp]['temp']=temp
        
    def getAllComponents(self,comp):
        ret={}
        ret['default']=self.components[comp]['temp']
        ret['comps']=self.components[comp]['subComp'].keys()
        return ret
    
    def getSettings(self,comp,subComp):
        return self.components[comp]['subComp'][subComp]
    
    ###SERVER FRAME
    def loadServers(self):
        return self.servers
    
    def getDefaultServer(self):
        return self.defaultServer
    
    def changeServer(self,old,new):
        self.removeServer(old[0],old[1])
        self.addServer(new[0],new[1],new[2])
        
    def removeServer(self,ip,port):
        self.servers=[s for s in self.servers if (s['ip'],s['port'])!=(ip,port)]
        if self.defaultServer==ip:
            self.defaultServer=None
        
    def addServer(self,ip,port,valid=True):
        for s in self.servers:
            if s['ip']==ip and s['port']==port:
                s['valid']=valid
                return
        self.servers.append({'ip':ip,'port':port,'valid':valid})
       
    def setDefaultServer(self,server):
        self.defaultServer=server
        
    def setActiveServer(self,ip,port,valid):
        for s in self.servers:
            if s['ip']==ip and s['port']==port:
                s['valid']=valid
                
    def getActiveServers(self):
        return [(s['ip'],s['port']) for s in self.servers if s['valid']]
    
    def getServers(self):
        return [(s['ip'],s['port'],s['valid']) for s in self.servers]
    
    ###UPNP FRAME
    def getUPNP(self):
        return self.upnp
    
    def setUPNP(self,on):
        self.upnp=on
        
    ###REMOTE PRODUCER FRAME
    def getRemotePreferences(self):
        return self.remotePrefs
    
    def setRemotePassword(self,password):
        self.remotePrefs['password']=password
        
    def setRemoteProducerDir(self,filename):
        self.remotePrefs['dir']=filename
        
    def setEnableRemoteProducer(self,on):
        self.remotePrefs['enable']=on
        

    ###DVB FRAME
    def getChannels(self):
        return self.channels
    
    def resetChannels(self,channels):
        self.channels=channels
      
    def changeChannel(self,old,new):
        self.removeChannel(old[0])
        self.addChannel(new[0],new[1],new[2])
        
    def removeChannel(self,name):
        self.channels.pop(name)

    def addChannel(self,name,loc,prog):
        self.channels[name]={}
        self.channels[name]['location']=str(loc)
        self.channels[name]['program']=int(prog)
    
    def writeBW(self,bw,ip=None):
        if not ip:
            ip=self.netChecker.localIp
        config.writeBW(bw,ip)
    
    def getConfigFiles(self):
        return self.filename,self.chFilename
    
    def saveFromRemoteConfig(self,file,chFile):
        config.create_remote_config(file,chFile,False)
        
    def getFirstRun(self):
        return config.getFirstRun()
    
if __name__=="__main__":
    Preferences(False)
        
        
        