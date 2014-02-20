class interface(object):
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

    specs={'bufsize':30,
                 'blocksec':10,
                 'reqInt':2}
    
    specsGui={'bufsize':{'name':'Buffer Size','tooltip':'The size of the buffer in blocks. Typical values 20-40'},
                      'blocksec':{'name':'Blocks/sec','tooltip':'One second of video is divided to that number of blocks. Typical values 5-20'},
                      'reqInt':{'name':'Request Interval','tooltip':'How often the peers request new blocks as a fraction of blocks/sec. Typical Values 2-4'}}
