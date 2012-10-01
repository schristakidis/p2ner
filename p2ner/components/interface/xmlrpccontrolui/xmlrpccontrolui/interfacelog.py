class InterfaceLog(object):
    def __init__(self):
        self.buffer=[]
        self.log=True
        
    def addRecord(self,record):
        if self.log:
            self.buffer.append(record)
        
    def getRecords(self):
        ret=self.buffer
        self.buffer=[]
        return ret
    
    def enableLogging(self,enable):
        self.log=enable