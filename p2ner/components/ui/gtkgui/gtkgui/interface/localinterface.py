from p2ner.abstract.interface import Interface

class Interface(Interface): 

    def initInterface(self, *args, **kwargs):
        pass

    def contactServers(self,servers):
        for s in servers:
            self.root.interface.contactServer(s)
            #d.addCallback(self.parent.getStream)
            #d.addErrback(self.failedXMLRPC)
 
        
    def subscribeStream(self,id,ip,port,outputMethod):
        self.root.interface.subscribeStream(id,ip,port,outputMethod)
        #d.addCallback(self.parent.succesfulSubscription,id)
        #d.addErrback(self.failedXMLRPC) 

    def stopProducing(self,id,repub):
        self.root.interface.stopProducing(id,repub)
        #d.addCallback(self.parent.stopProducing,id)
        #d.addErrback(self.failedXMLRPC) 
        
    def unregisterStream(self,id):
        self.root.interface.unregisterStream(id)
        #d.addCallback(self.parent.unregisterStream,id)
        #d.addErrback(self.failedXMLRPC) 
        
    def startProducing(self,id,type):
        self.root.interface.startProducing(id)
        #d.addCallback(self.parent.changeStreamStatus,id,type)
        #d.addErrback(self.failedXMLRPC)
        
    def startRemoteProducer(self,id,type):
        self.root.interface.startRemoteProducer(id)
        #d.addCallback(self.parent.changeStreamStatus,id,type)
        #d.addErrback(self.failedXMLRPC)
        #self.parent.changeStreamStatus(d,id,type)
        
    def registerStream(self,settings,inputMethod,outputMethod):   
        self.root.interface.registerStream(settings,inputMethod,outputMethod)
        #d.addCallback(self.parent.registerStream)
        #d.addErrback(self.failedXMLRPC)
        
    def getComponentsInterfaces(self,comp):
        self.root.interface.getComponentsInterfaces(comp)
        
    def startConverting(self,gui,dir,filename,videorate,subs,subsFile,subsEnc):
        self.root.interface.startConverting(gui,dir,filename,videorate,subs,subsFile,subsEnc)

    def getConverterStatus(self,gui,id):
        self.root.interface.getConverterStatus(gui,id)
    
    def abortConverter(self,id):
        self.root.interface.abortConverter(id)

    def send(self,rcom,arg,lcom):
        rcom=eval('self.root.interface.'+rcom)
        if arg:
            lcom(rcom(arg))
        else:
            lcom(rcom())
            
    def exiting(self):
        self.root.exiting()
        
    def getAvailableStatistics(self,func):
        func(self.root.interface.getStatistics())

    def getStatValues(self,func,stats):
        func(self.root.interface.getStatValues(stats))
        
    def startMeasurement(self,ip,gui):
        self.root.startBWMeasurement(ip,gui)
        
    def setBW(self,bw):
        self.root.setBW(bw)
    
    def checkNetwork(self):
        self.root.interface.checkNetwork()
        
