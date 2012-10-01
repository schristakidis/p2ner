# -*- coding: utf-8 -*-

from p2ner.base.Consts import MessageCodes as MSG
from construct import Container
from p2ner.base.ControlMessage import ControlMessage
import time

class RTTMessage(ControlMessage):
    type = "rttmessage"
    code = MSG.RTT
    ack = False
    
    def initMessage(self, *args, **kwargs):
        self.interface.registerStat('sendBw')
        self.interface.registerStat('rtt')
        self.interface.registerStat('drtt')
        self.interface.registerStat('recBw')
        self.interface.registerStat('blockSize')
        self.serialCount=-1
        
    def trigger(self, message):
        return True

    def action(self, message, peer):
        if message.blockId<self.serialCount:
            print 'received out of sunc rtt message ',message.blockId,self.serialCount
            self.serialCount=message.blockId
            
        peer.rtt1=time.time()-message.rtt
        peer.rtt2=time.time()-message.lrtt
        #print peer.rtt1,peer.rtt2,peer.rtt2-peer.rtt1
        
        """
        if peer.rtt2>1.2*peer.rtt1:
            peer.decreaseBw=True
            peer.bw=0.8*message.sendrate
            #print 'DECREASING BW from ',message.sendrate,' to ',peer.bw, ' for ',peer
            peer.bw=0.8*message.sendrate
        else:
            if peer.decreaseBw:
                peer.bw=1.1*message.sendrate
            else:
                peer.bw=2*message.sendrate
            #print 'INCREASING BW from ',message.sendrate,' to ',peer.bw,' for ',peer
         """
        
        self.interface.setStat('sendBw',peer.bw,time.time())  
        self.interface.setStat('rtt',peer.rtt1,time.time())  
        self.interface.setStat('drtt',peer.rtt2-peer.rtt1,time.time())  
        self.interface.setStat('recBw',message.rate,time.time())  
        self.interface.setStat('blockSize',message.size,time.time())  
        
        #peer.bw=peer.bw*1000
        
         
            
        """    
        peer.rtt=time.time()-message.rtt-1400/peer.bw
        if peer.rtt<0:
            peer.rtt=0.001
        peer.meanRtt.append(peer.rtt)
        peer.meanRtt=peer.meanRtt[-10:]
        #if time.time()-message.rtt>1.2*peer.rtt:
        #    print 'dddddddddddddddddddddd ',time.time()-message.rtt,peer.rtt,peer.meanRtt
        
        print 'rttt::::::',peer.rtt
        print time.time(),message.rtt,1400/peer.bw,peer.bw
        if message.rate<0.70*message.sendrate:
            peer.meanBw.append(message.rate)
            peer.meanBw=peer.meanBw[-10:]
            peer.decreaseBw=True
            if len(peer.meanBw)>5:
                meanBw=0
                for b in peer.meanBw:
                    meanBw +=b
                meanBw=meanBw/len(peer.meanBw)
                peer.bw=1.1*meanBw
                print 'mean bWWWWWWW ',peer.meanBw,' for ',peer
            else:
                peer.bw=1.1*message.rate
            print 'DECREASING BW from ',message.sendrate,' to ',peer.bw, ' for ',peer
        else:
            if peer.decreaseBw:
                peer.bw=1.1*message.sendrate
            else:
                peer.bw=2*message.sendrate
            print 'INCREASING BW from ',message.sendrate,' to ',peer.bw,' for ',peer 
        
     
        peer.bw=peer.bw*1000    
        
        meanRtt=0
        for r in peer.meanRtt:
            meanRtt +=r
        meanRtt=meanRtt/len(peer.meanRtt)
        if peer.rtt>1.5*meanRtt:
            print 'CONGESTION????????'
            print peer.rtt,peer.meanRtt
            peer.bw=0.8*peer.bw
        """