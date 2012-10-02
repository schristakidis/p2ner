from p2ner.core.namespace import Namespace, initNS
from messages.messages import  ChatterMessage,ChatMessage

class ChatServer(Namespace):
    @initNS
    def __init__(self):
        self.chatRooms={}
        self.registerMessages()
        
    def registerMessages(self):
        self.messages = []
        self.messages.append(ChatterMessage())
        self.messages.append(ChatMessage())
        
    def newRoom(self,id):
        self.chatRooms[id]={}
        
    def removeRoom(self,id):
        self.chatRooms.pop(id)
        
    def newMessage(self,id,message,peer):
        if id not in self.chatRooms.keys():
            print 'received chatter message for a non existing room'
            return
        peers=[p  for p in self.chatRooms[id].keys() if p!=peer]
        ChatMessage.send(id,(peer.getIP(),peer.getPort()),message,peers,self.controlPipe)
            
    def newChatter(self,id,username,new,peer):
        if id not in self.chatRooms.keys():
            print 'received chatter for a non existing room'
            print id
            print self.chatRooms.keys()
            return
        print self.chatRooms[id].values()
        if new:
            if self.chatRooms[id].values():
                ChatterMessage.send(id,[(username,peer.getIP(),peer.getPort())],True,self.chatRooms[id].keys(),self.controlPipe)
                users=[(v,k.getIP(),k.getPort()) for k,v in self.chatRooms[id].items()]
                ChatterMessage.send(id,users,True,peer,self.controlPipe)
            self.chatRooms[id][peer]=username
        else:
            self.chatRooms[id].pop(peer)
            if self.chatRooms[id].keys():
                ChatterMessage.send(id,[(username,peer.getIP(),peer.getPort())],False,self.chatRooms[id].keys(),self.controlPipe)
            
