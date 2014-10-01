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
    specs={'baseNumNeigh':8,
           'superNumNeigh':8,
           'interNumNeigh':8,
                  'swapFreq':3}

    specsGui={'baseNumNeigh':{'name':'Number Of Base Neighbours','tooltip':'The number of neighbours each base peer should have. Typical values 4-10'},
              'superNumNeigh':{'name':'Number Of Super Neighbours','tooltip':'The number of neighbours each super peer should have. Typical values 4-10'},
              'interNumNeigh':{'name':'Number Of Inter Neighbours','tooltip':'The number of super neighbours each base peer should have. Typical values 4-10'},
                       'swapFreq':{'name':'Swap Frequency','tooltip':'The frequency of neighbor swapping'}}

