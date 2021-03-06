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

class interface(object):
    specs={'videoRate':0,'audio':'pulse','width':360,'height':240}
    
    specsGui={'videoRate':{'name':'Video Rate','tooltip':'The quality of the transcoded video in KBps. 0 for default quality'},
                      'audio':{'name':'Audio Input','tooltip':'Audio Input device. Only for camera input on linux'},
                      'width':{'name':'Width','tooltip':'The width of the encoded video'},
                      'height':{'name':'Height','tooltip':'The height of the encoded video'}}

                      
