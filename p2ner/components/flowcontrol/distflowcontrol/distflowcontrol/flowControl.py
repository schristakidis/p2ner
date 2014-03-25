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

from p2ner.abstract.flowcontrol import FlowControl
from twisted.internet import reactor
import time
import bora
import pprint

class DistFlowControl(FlowControl):
    def initFlowControl(self,*args,**kwargs):
        self.peers={}
        self.TsendRef=0.1
        self.Tsend=self.TsendRef
        self.k=0.4
        self.ackHistory=[]
        self.bwHistory=[]
        self.errorHistory=[]
        self.historySize=int(1/self.Tsend)
        self.umax=0
        self.maxumax=self.umax
        self.u=4
        self.errorPhase=False
        self.recoveryPhase=False

    def update(self,data):
        ackSum=0
        errSum=0
        print data
        for peer in data['peer_stats']:
            p=(peer.host,peer.port)
            if p not in self.peers:
                self.peers.append(p)
                self.peers[p]={}

            self.peers[p]['lastRtt']=peer['avgRTT']
            self.peers[p]['lastStt']=peer['avgSTT']
            self.peers[p]['minRtt']=peer['minRTT']
            self.peers[p]['minStt']=peer['minSTT']
            self.peers[p]['errorRtt']=peer['errRTT']
            self.peers[p]['errorStt']=peer['errSTT']
            if not self.peers[p]['errorStt']:
                self.peers[p]['errorStt']=self.peers[p]['minStt']+0.05
                self.peers[p]['errorRtt']=self.peers[p]['minRtt']+0.05

            ackSum+=peer['acked_last']
            errSum+=peer['error_last']

        self.ackHistory.append(ackSum)
        self.errorHistory.append(errSum)
        if len(self.ackHistory)>self.historySize:
            self.ackHistory=self.ackHistory[-self.historySize:]
            self.errorHistory=self.errorHistory[-self.historySize:]

        self.lastAckSize=self.ackHistory[-1]

        lastAck=data['last_ack']
        executeAlgo=True
        if lastAck:
            self.rtt=lastAck['RTT']
            self.stt=lastAck['STT']
            lastPeer=(lastAck['host'],lastAck['port'])
            self.minRtt=self.peers[lastPeer]['minRtt']
            self.minStt=self.peers[lastPeer]['minStt']
            self.errRtt=self.peers[lastPeer]['errorRtt']
            self.errStt=self.peers[lastPeer]['errorStt']


            errors=sum(self.errorHistory)
            acks=sum(self.ackHistory)
            self.errorsPer=100.0*errors/acks

            self.lastSentTime=lastAck['sent']
            self.lastAckedSent=lastAck['seq']
            self.lastSleepTime=lastAck['sleep']*10**(-6)
            self.lastNack=data['last_nack']
        else:
            executeAlgo=False
            self.minRtt=0
            self.minStt=0
            self.errRtt=0
            self.errStt=0
            self.stt=0
            self.rtt=0

        self.qDelay=self.stt-self.minStt
        self.qRef=2*(self.errStt-self.minStt)/4
        self.refStt=self.minStt+self.qRef

        lastData=data['sent_data']
        self.totalDataSent=lastData['O_DATA_COUNTER']
        self.ackSent=lastData['O_ACK_DATA_COUNTER']

        try:
            self.ackRate = 1.0*sum(self.ackHistory)/(len(self.ackHistory)*self.Tsend)
        except:
            self.ackRate=0

        if executeAlgo:
            self.setUmax()

    def setUmax(self):
        tumax = sorted(self.bwHistory)
        try:
            self.umax = tumax[-3]
        except:
            self.umax = tumax[0]
        self.lastBW = self.bwHistory[-1]
        self.maxumax=self.umax

        if not self.errorPhase and self.errorsPer>5:
            self.errorPhase=True
            self.recoveryPhase=False

        if self.errorPhase:
            self.umax=self.umax/2
            self.prevumax=self.maxumax/30

        if self.errorPhase and self.stt<self.refStt and self.errorsPer<=5:
                self.errorPhase=False
                self.recoveryPhase=True
                self.umax=self.maxumax

        if self.recoveryPhase:
            self.umax=self.umax/2+self.prevumax
            self.prevumax += self.maxumax/30
            if self.umax > self.maxumax:
                self.recoveryPhase=False
                self.umax=self.maxumax

        self.setU()

    def setU(self):
        nackedSends=self.lastNack-self.lastAckedSent
        self.actualU=self.umax-self.ackSent
        predictedConsumeBw=self.actualU*(time.time()-self.lastSentTime-self.lastSleepTime)
        self.difBw=nackedSends*1408-predictedConsumeBw

        ynl=self.qDelay*self.umax
        yn=ynl+self.difBw
        yref=self.qRef*self.actualU
        self.controlBw=(1-self.k)*(yref-yn)
        self.u=self.controlBw + self.actualU*self.TsendRef
        self.u=self.u/1408
        if round(self.u)<=0:
            self.u=1

        self.Tsend=self.TsendRef*round(self.u)/self.u
        self.u=int(round(self.u))
        print self.peers
        print self.u
        print self.Tsend

    def bws_thread(self):
        interval=self.TsendRef*10**6
        pp = pprint.PrettyPrinter(indent=4)
        for b in bora.bwsiter(interval):
            pp.pprint(b)
            reactor.callInThread(self.update,b)
            #interval=self.Tsend*10**6

            reactor.callFromThread(bora.bws_set, 100000, 1000000)





