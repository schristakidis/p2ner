from p2ner.core.namespace import Namespace, initNS
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
       
            
            

        
        