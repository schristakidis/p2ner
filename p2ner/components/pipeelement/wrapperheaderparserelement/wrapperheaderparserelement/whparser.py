
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
