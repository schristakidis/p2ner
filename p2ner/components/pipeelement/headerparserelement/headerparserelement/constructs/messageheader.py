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


class IpAddressAdapter(Adapter):
    def _encode(self, obj, context):
        return "".join(chr(int(b)) for b in obj.split("."))
    def _decode(self, obj, context):
        return ".".join(str(ord(b)) for b in obj)

MessageHeader = Struct("header",
        UBInt16("port"),
        Flag("ack"),
        UBInt16("seq"),
        UBInt8("code"),
        Flag("lip"),
        If(lambda ctx: ctx["lip"],
            IpAddressAdapter(Bytes("localIP",  4))
           ),
        )

MessageHeaderSimple = Struct("header",
        UBInt16("port"),
        Flag("ack"),
        UBInt16("seq"),
        UBInt8("code"),
        Flag("lip"),
        )

MessageHeaderIp = Struct("header",
        UBInt16("port"),
        Flag("ack"),
        UBInt16("seq"),
        UBInt8("code"),
        Flag("lip"),
        IpAddressAdapter(Bytes("localIP",  4)),
        )
