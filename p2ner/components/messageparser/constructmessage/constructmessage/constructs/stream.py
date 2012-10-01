# -*- coding: utf-8 -*-

from construct import *
from p2ner.base.Stream import Stream
from cPickle import dumps, loads
import sys

SBaseMessageStruct = Struct('scheduler',
        UBInt16("length"),
        MetaField("scheduler",  lambda ctx: ctx["length"]),
        )

class SBaseMessageAdapter(Adapter):
        def _encode(self, obj, context):
            msg = dumps(obj, 2)
            return Container(scheduler = msg,  length = len(msg))
        def _decode(self, obj, context):
            return loads(obj.scheduler)
        
OBaseMessageStruct = Struct("overlay",
        UBInt16("length"),
        MetaField("overlay",  lambda ctx: ctx["length"]),
        )

class OBaseMessageAdapter(Adapter):
        def _encode(self, obj, context):
            msg = dumps(obj, 2)
            return Container(overlay = msg,  length = len(msg))
        def _decode(self, obj, context):
            return loads(obj.overlay)
        
class StreamAdapter(Adapter):
    def _encode(self,  obj,  ctx):
 
        return Container(id =int(obj.id),  
                         title = str(obj.title),  
                         starttime =int(obj.startTime),  
                         description = str(obj.description), 
                         serverIP=str(obj.server[0]),
                         serverPort=int(obj.server[1]),
                         startable=bool(obj.startable),
                         republish=bool(obj.republish),
                         overlay=dict(obj.overlay),
                         scheduler=dict(obj.scheduler),
                         type=str(obj.type),
                         author=str(obj.author),
                         filename=str(obj.filename),
                         password=str(obj.password),
                         live=bool(obj.live))

    def _decode(self,  obj,  ctx):
        stream = Stream(id=obj.id,  
                      title=obj.title,  
                      startTime = obj.starttime,   
                      description = obj.description,  
                      server= (obj.serverIP,obj.serverPort),
                      startable=obj.startable,
                      republish=obj.republish,
                      overlay=obj.overlay,
                      scheduler=obj.scheduler,
                      type=obj.type,
                      author=obj.author,
                      filename=obj.filename,
                      live=obj.live,
                      password=obj.password,
                      )
        return stream


StreamStruct = Struct( "stream", 
                   UBInt32("id"),
                   CString("title"), 
                   UBInt32("starttime"),  
                   CString("description"), 
                   CString('serverIP'),
                   UBInt32('serverPort'),
                   UBInt8('startable'),
                   UBInt8('republish'),
                   SBaseMessageAdapter(SBaseMessageStruct),
                   OBaseMessageAdapter(OBaseMessageStruct), 
                   CString('filename'),
                   CString('type'),
                   CString('author'),
                   CString('password'),
                   UBInt8('live')
                   )


        
if __name__ == "__main__":
    c =  Container(id = 11,  
                         title = 'title',  
                         starttime = 0,  
                         bitrate = 39999,  
                         buffersize = 25,  
                         blocksec = 5,  
                         numofneigh = 3, 
                         description = "desc", 
                         reqinterval = 2)
    binstream = StreamStruct.build(c)
    stream =  StreamAdapter(StreamStruct).parse(binstream)
    print stream
    stream.id = 222
    binstream = StreamStruct.build(c)
    stream =  StreamAdapter(StreamStruct).parse(binstream)
    print stream
    
    print repr(StreamStruct.build(c))
