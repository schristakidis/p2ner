
from p2ner.abstract.pipeelement import PipeElement
from twisted.internet import reactor
import struct

class WrapperHeaderParserElement(PipeElement):

    def initElement(self, *args, **kwargs):
        self.log.info('WrapperHeaderParser loaded')
    
    def send(self, res, msg, data, peer):
        h=struct.pack('!?',False)
        h=''.join([h,res])
        tPipe=self.trafficPipe.getElement(name="UDPPortElement")
        tPipe.send(h,msg,data,peer)
        self.breakCall()
        
    def receive(self,todecode,(host, port), recTime):
        d=self.forwardprev("receive", (host, port), recTime,dataPort=True)
        d.callback(todecode)