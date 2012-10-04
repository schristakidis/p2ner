# -*- coding: utf-8 -*-
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


from construct import Container
from constructs.messages import MSG_TYPES

def encodemsg(msg, content):
    if msg.type not in MSG_TYPES:
        print msg.type, "not in",  MSG_TYPES

    #content.header=Container(code=msg.code, ack=msg.ack) #why again?

    try:
        encoded = MSG_TYPES[msg.type].build(content)
    except:
        print MSG_TYPES[msg.type].build(content)

    return encoded