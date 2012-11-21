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


from p2ner.abstract.input import Input
import random

class RandomInput(Input):
    
    def initInput(self, *args, **kwargs):
        print self.stream
        self.input=kwargs['input']
        self.videoRate=self.input['videoRate']*1024
        blockSec=self.stream.scheduler['blocksec']
        print 'rate:',self.videoRate
        print 'NB:',blockSec
        blocksize = int(self.videoRate/blockSec/8.0)
        print 'block size:',blocksize
        b = ""              
        for i in xrange(blocksize):
            b+=chr(random.randint(0,255))
        self.block = b
    
    def read(self):
        return self.block
    
    def start(self):
        pass
        
    def isRunning(self):
        return True
    
    def stop(self):
        return True
    