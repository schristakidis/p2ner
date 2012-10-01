from p2ner.base.ControlMessage import ControlMessage
from p2ner.base.Consts import MessageCodes as MSG
from twisted.internet import reactor


class KeepAliveMessage(ControlMessage):
    type = "basemessage"
    code = MSG.KEEP_ALIVE
    ack = True

    def trigger(self, message):
        return True
    
    def action(self, message, peer):
        print 'keep alive message received'
        return True  
    

