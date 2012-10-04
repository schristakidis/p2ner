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


from construct import *
from cPickle import dumps, loads

BaseMessageStruct = Struct("message",
        UBInt16("length"),
        MetaField("message",  lambda ctx: ctx["length"]),
        )

class BaseMessageAdapter(Adapter):
        def _encode(self, obj, context):
            msg = dumps(obj, 2)
            return Container(message = msg,  length = len(msg))
        def _decode(self, obj, context):
            return loads(obj.message)
