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


from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG

class ClientStoppedMessage(ControlMessage):
    type = "sidmessage"
    code = MSG.CLIENT_STOPPED
    ack = True
    
    def trigger(self, message):
        return message.streamid == self.stream.id


    def action(self, message, peer):
            self.log.debug('received clientStopped message from %s',peer)
            self.overlay.removeNeighbour(peer)
            found=False
            for ov in self.overlays.values():
                if ov.isNeighbour(peer):
                    found=True
                    break
            if not found:
                print 'removing ',peer,' from known peers'
                print self.knownPeers
                self.log.debug('remove %s from known peers',peer)
                self.knownPeers.remove(peer)
