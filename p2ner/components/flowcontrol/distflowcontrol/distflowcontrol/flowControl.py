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
from twisted.internet import reactor,task
import time
import bora
import pprint

def bws_thread(flowcontrol, interval):
        pp = pprint.PrettyPrinter(indent=4)
        for b in bora.bwsiter(interval):
            # pp.pprint(b)
            reactor.callFromThread(flowcontrol.update,b)

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
        self.bwHistorySize=50
        self.umax=10000
        self.maxumax=self.umax
        self.u=4
        self.errorPhase=False
        self.recoveryPhase=False
        self.loopingCall=task.LoopingCall(self.sendBWstats)
        self.stats=[]
        self.count=0
        self.errorsPer=0
        self.difBw=0
        self.controlBw=0
        self.actualU=0
        self.lastBW=0



    def start(self):
        reactor.callInThread(bws_thread, self, self.TsendRef)
        self.loopingCall.start(0.1)

    def update(self,data):
        ackSum=0
        errSum=0
        for peer in data['peer_stats']:
            p=(peer["host"],peer["port"])
            if p not in self.peers:
                self.peers[p]={}

            self.peers[p]['lastRtt']=peer['avgRTT']*pow(10,-6)
            self.peers[p]['lastStt']=peer['avgSTT']*pow(10,-6)
            self.peers[p]['minRtt']=peer['minRTT']*pow(10,-6)
            self.peers[p]['minStt']=peer['minSTT']*pow(10,-6)
            self.peers[p]['errorRtt']=peer['errRTT']*pow(10,-6)
            self.peers[p]['errorStt']=peer['errSTT']*pow(10,-6)
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
            self.rtt=lastAck['RTT']*pow(10,-6)
            self.stt=lastAck['STT']*pow(10,-6)
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
        else:
            self.send_bw()

    def setUmax(self):
        bw=bora.get_bw_msg()
        for b in bw:
            self.bwHistory.append(b['bw'])
        if len(self.bwHistory)>self.bwHistorySize:
            self.bwHistory=self.bwHistory[-self.bwHistorySize:]

        if not self.bwHistory:
            self.send_bw()
            return

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
        print 'uuuuuuuuuuuu:',self.u
        print 'tsenddddd:',self.Tsend
        print 'bwwwwwwwwww:',int(self.u*1408/self.Tsend)
        print 'reported bw:',self.lastBW
        print '---------------------------'
        self.send_bw()

    def send_bw(self):
        print "SET BW", int(self.u*1408/self.Tsend), int(self.Tsend*pow(10,6))
        bora.bws_set(int(self.u*1408/self.Tsend), int(self.Tsend*pow(10,6)) )
        self.saveStats()

    def sendBWstats(self):
        try:
            bwStats=bora.get_bw_stats()
        except:
            return

        send=[]
        for p in bwStats:
            estBw=[]
            peer=(p['ip'],p['port'])
            for b in p['list']:
                estBw.append(b['bw'])

            if len(estBw):
                estBw.sort(reverse=True)
                cat=[]
                temp=[]
                for e in estBw:
                    if not len(temp):
                        temp.append(e)
                    elif e+0.1*e>temp[0]:
                        temp.append(e)
                    else:
                        cat.append(temp)
                        temp=[]
                if len(temp):
                    cat.append(temp)

                est=max([(len(b),b) for b in cat])
                est=est[1]
            else:
                continue

            bw=sum(est)/len(est)
            t={}
            t['ip']=peer[0]
            t['port']=peer[1]
            t['bw']=bw
            send.append(t)

        if send:
            bora.send_bw_msg(send)

    def saveStats(self):
        temp={}
        temp['x']=self.count
        temp['u']=self.u
        temp['umax']=self.umax
        temp['rtt']=self.rtt
        temp['stt']=self.stt
        temp['minStt']=self.minStt
        temp['minRtt']=self.minRtt
        temp['errStt']=self.errStt
        temp['errRtt']=self.errRtt
        temp['ackRate']=self.ackRate
        temp['refStt']=self.refStt
        temp['qRef']=self.qRef
        temp['qDelay']=self.qDelay
        temp['errorP']=self.errorsPer
        temp['Tsend']=self.Tsend
        temp['difBw']=self.difBw
        temp['controlBW']=self.controlBw
        temp['actualU']=self.actualU
        temp['lastBW']=self.lastBW
        self.count+=1
        self.stats.append(temp)
        if len(self.stats)>20:
            self.stats.pop(0)

    def getStats(self):
        ret=self.stats[:]
        self.stats=[]
        return ret

