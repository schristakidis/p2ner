from p2ner.core.namespace import Namespace, initNS
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

from messages.messages import  ChatterMessage,ChatMessage

class ChatClient(Namespace):
    @initNS
    def __init__(self):
        self.chatRooms={}
        self.registerMessages()
        
    def registerMessages(self):
        self.messages = []
        self.messages.append(ChatterMessage())
        self.messages.append(ChatMessage())
        
    def joinChatRoom(self,id,username,server):
        self.chatRooms[id]={}
        ChatterMessage.send(id,username,True,server,self.controlPipe)
        
    def leaveChatRoom(self,id,username,server):
        self.chatRooms.pop(id)
        ChatterMessage.send(id,username,False,server,self.controlPipe)
        
    def newMessage(self,id,message,peer):
        if id not in self.chatRooms.keys():
            print 'received chatter message for a non existing room'
            return
        self.interface.newChatMessage(id,message,peer)
        
    def sendChatMessage(self,id,message,server):
        ChatMessage.send(id,message,server,self.controlPipe)
        
            
    def newChatter(self,id,username,new):
        if id not in self.chatRooms.keys():
            print 'received chatter for a non existing room'
            return
        self.interface.newChatter(id,username,new)
       
            
            

        
        