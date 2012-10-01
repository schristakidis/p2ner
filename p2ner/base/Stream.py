# -*- coding: utf-8 -*-

#from p2ner.util.logger import LOG as log
from hashlib import md5
from time import strftime,localtime

class Stream(object):

    def __init__(self, server = None, id = 0, type = 0, title = "", author='',live=False,startable=False,startTime = 0, password='', republish=False,overlay='',scheduler='',filename='', description= ""):

        self.server = server
        self.id = id
        self.type = type
        self.title = title
        self.author=author
        self.startable=startable
        self.startTime = startTime
        self.password=password
        self.republish=republish
        self.overlay=overlay
        self.scheduler=scheduler
        self.filename=filename
        self.description = description
        self.live=live
        
    def __repr__(self):
        c= "".join(["STREAM ID:", str(self.id), 
                        ', serverIP:',str(self.server[0]),
                        ', serverPort:',str(self.server[1]),
                        ', startable:', str(self.startable),
                        ', republish:', str(self.republish),
                        ', filename:', str(self.filename),
                        ", type:", str(self.type), 
                        ", author:",str(self.author),
                        ", title:", str(self.title), 
                        ", startTime:", str(self.startTime), 
                        ', description:', str(self.description),
                        ', live:',str(self.live),
                        ", password:",str(self.password)])
        for k,v in self.scheduler.items():
            if k!='component':
                c=''.join([c,', ',k,':',str(v)])
            else:
                c=''.join([c,', scheduler:',str(v)])
        for k,v in self.overlay.items():
            if k!='component':
                c=''.join([c,', ',k,':',str(v)])
            else:
                c=''.join([c,', overlay:',str(v)])
        return c
    
    def streamHash(self):
        hashstring= "".join([str(self.server[0]),
                        str(self.server[1]),
                        str(self.filename),
                        str(self.type), 
                        str(self.author),
                        str(self.title), 
                        str(self.startTime), 
                        str(self.description)])
        for k,v in self.scheduler.items():
                hashstring=''.join([hashstring,str(v)])
        for k,v in self.overlay.items():
                hashstring=''.join([hashstring,str(v)])
        return md5(hashstring).hexdigest()
    
    def getDesc(self):
        desc='Stream ID:'+str(self.id)+'\n'
        desc +='Author:'+self.author+'\n'
        desc +='Title:'+self.title+'\n'
        desc +='Description:'+self.description+'\n'
        desc +='Type:'+self.type+'\n'
        desc +='Server IP:'+self.server[0]+'\n'
        desc +='Server Port:'+str(self.server[1])+'\n'
        desc +='Live:'+str(bool(self.live))+'\n'
        desc +='Startable:'+str(bool(self.startable))+'\n'
        starttime='not valid'
        if self.startTime!=0:
            starttime=strftime('%H:%M %A %d %m %y',localtime(self.startTime))
        desc +='Start Time:'+starttime+'\n'
        pswd='No'
        pswd='No'
        if self.password:
            pswd='Yes'
        desc +='Password:'+pswd+'\n'
        desc +='Rebublish:'+str(bool(self.republish))+'\n'
        desc +='\n'+'Stream Settings'+'\n'
        desc +='Filename:'+str(self.filename)+'\n'
        desc +='Overlay:'+self.overlay['component']+'\n'
        for k,v in self.overlay.items():
            if k!='component':
                desc +=k+':'+str(v)+'\n'
        desc +='Scheduler:'+self.scheduler['component']+'\n'
        for k,v in self.scheduler.items():
            if k!='component':
                desc +=k+':'+str(v)+'\n'
        

        return desc

    def getServer(self):
        return self.server
        
if __name__ == "__main__":
    a=Stream()
    print a
