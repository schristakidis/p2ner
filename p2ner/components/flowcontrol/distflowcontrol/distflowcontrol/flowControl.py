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
from math import ceil
from twisted.internet.threads import deferToThread

def bws_thread(flowcontrol, interval):
        pp = pprint.PrettyPrinter(indent=4)
        for b in bora.bwsiter(interval):
            #pp.pprint(b)
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
        self.idle=0
        self.idleHistorySize=5
        self.ackRatioHistory=[]
        self.calculatedmin=0
        self.idleSttStatus=0
        self.idleAck=0
        self.lastIdlePacket=0
        self.idlePackets=[]
        self.recHistory=[]
        self.qDelayErr=0.1
        self.qHistorySize=10
        self.qDelayHistory=[]
        self.umaxHistory=[]
        self.umaxHistorySize=10
        self.wrongStt=0



    def start(self):
        reactor.callInThread(bws_thread, self, self.TsendRef)
        self.loopingCall.start(0.1)

    def checkIdle(self):
        const=True
        idle=False
        self.idleSttStatus=0

        temp={}
        for stt,p in self.recHistory:
            if p not in temp.keys():
               temp[p]=[]
            temp[p].append(stt)

        for p,v in temp.items():
            if not const:
                break
            lstt=v[0]
            for stt in v[1:]:
                if stt>1.1*lstt or stt<0.9*lstt:
                    const=False
                    break

        if const:
            self.idleSttStatus=1
            first=self.ackRatioHistory[0]
            last=self.ackRatioHistory[-1]
            # self.idleAck=max((1.0*(last-first)/last),(1.0*(first-last)/first))
            self.idleAck=1.0*(last-first)/last

            line=False
            if self.idleAck>0.1:
                a=1.0*(last-first)/len(self.ackRatioHistory)
                line=True
                for x in range(len(self.ackRatioHistory)):
                    point1=0.9*first+a*x
                    point2=1.1*first+a*x
                    if self.ackRatioHistory[x]<point1 or self.ackRatioHistory[x]>point2:
                        line=False

            if line:
                idle=True
            else:
                isIdle=True
                for i in self.idlePackets:
                    if i<=1:
                        isIdle=False
                        break
                if isIdle:
                    idle=True

            if idle and not self.errorPhase:
                self.idle+=1
                if self.idle>2:
                    for p in temp.keys():
                        self.peers[p]['calcMin']=min(temp[p])
                        self.peers[p]['calcMinTime']=time.time()
                    self.idle=2
            else:
                self.idle=0
        else:
            self.idle=0

    def checkMinStt(self,data):
        shouldCalculateMin=[]
        for peer in data['peer_stats']:
            p=(peer["host"],peer["port"])
            if not 'calcMin' in self.peers[p].keys():
                if not 'waitingMin' in self.peers[p].keys():
                    self.peers[p]['waitingMin']=0

                if not self.peers[p]['waitingMin']:
                    shouldCalculateMin.append(p)
                else:
                    self.peers[p]['waitingMin']-=1

        goodPeer=None
        if shouldCalculateMin:
            try:
                goodPeer=max([(v['calcMinTime'],p) for p,v in self.peers.items() if 'calcMin' in v.keys()])[1]
            except:
                pass

        if goodPeer:
            for p in shouldCalculateMin:
                self.peers[p]['waitingMin']=10
                d=deferToThread(bora.send_cookie,goodPeer[0],goodPeer[1],p[0],p[1])
                d.addCallback(self.updateMin,goodPeer,p)

    def updateMin(self,data,goodPeer,peer):
        print 'update minnnnnnnnnnnnn'
        print 'goodPeer:',goodPeer
        print 'peer:',peer
        print data
        for line in data:
            if line['host']==goodPeer[0] and line['port']==goodPeer[1]:
                goodStt=line['STT']*pow(10,-6)
            elif line['host']==peer[0] and line['port']==peer[1]:
                stt=line['STT']*pow(10,-6)
            else:
                print 'error in update minnnnnnnnnnnn'
                return

        delay=goodStt-self.peers[goodPeer]['calcMin']
        self.peers[peer]['calcMin']=stt-delay
        self.peers[peer]['waitingMin']=0



    def checkWrongStt(self):
        self.wrongStt=0
        if not self.qDelayHistory:
            return

        thres=0.01
        avgDelay=sum(self.qDelayHistory)/len(self.qDelayHistory)
        secondNorm=sum([(d-avgDelay)**2 for d in self.qDelayHistory])/len(self.qDelayHistory)
        if secondNorm>thres**2:
            self.wrongStt=1




    def update(self,data):
        ackSum=0
        errSum=0
        for peer in data['peer_stats']:
            p=(peer["host"],peer["port"])
            if p not in self.peers:
                self.peers[p]={}

            self.recHistory.append((peer['avgSTT']*pow(10,-6),p))
            self.recHistory=self.recHistory[-self.idleHistorySize:]

            self.peers[p]['lastRtt']=peer['avgRTT']*pow(10,-6)
            self.peers[p]['lastStt']=peer['avgSTT']*pow(10,-6)
            self.peers[p]['minRtt']=peer['minRTT']*pow(10,-6)
            self.peers[p]['minStt']=peer['minSTT']*pow(10,-6)
            self.peers[p]['errorRtt']=peer['errRTT']*pow(10,-6)
            self.peers[p]['errorStt']=peer['errSTT']*pow(10,-6)
            if not self.peers[p]['errorStt']:
                self.peers[p]['errorStt']=self.peers[p]['minStt']+0.05
                self.peers[p]['errorRtt']=self.peers[p]['minRtt']+0.05

            if peer['error_last']:
                self.qDelayErr=(peer['errSTT']-peer['minSTT'])*pow(10,-6)


            ackSum+=peer['acked_last']
            errSum+=peer['error_last']

        if not self.peers:
            self.send_bw()
            return

        self.ackHistory.append(ackSum)
        self.errorHistory.append(errSum)
        if len(self.ackHistory)>self.historySize:
            self.ackHistory=self.ackHistory[-self.historySize:]
            self.errorHistory=self.errorHistory[-self.historySize:]

        if len(self.ackRatioHistory)>3:
            self.checkIdle()

        self.checkMinStt(data)

        lastAck=data['last_ack']
        executeAlgo=True
        if lastAck:
            self.rtt=lastAck['RTT']*pow(10,-6)
            self.stt=lastAck['STT']*pow(10,-6)
            lastPeer=(lastAck['host'],lastAck['port'])
            self.minRtt=self.peers[lastPeer]['minRtt']
            try:
                self.minStt=self.peers[lastPeer]['calcMin']
            except:
                self.minStt=self.peers[lastPeer]['minStt']
            self.errRtt=self.peers[lastPeer]['errorRtt']
            # self.errStt=self.peers[lastPeer]['errorStt']
            self.errStt=self.minStt+self.qDelayErr


            errors=sum(self.errorHistory)
            acks=sum(self.ackHistory)
            self.errorsPer=100.0*errors/acks

            self.lastSentTime=lastAck['sent']
            self.lastAckedSent=lastAck['seq']
            self.lastSleepTime=lastAck['sleep']*pow(10,-6)
            self.lastNack=data['last_nack']

            try:
                self.calculatedmin=self.peers[lastPeer]['calcMin']
            except:
                self.calculatedmin=0
        else:
            executeAlgo=True
            """
            self.minRtt=0
            self.minStt=0
            self.errRtt=0
            self.errStt=0
            self.stt=0
            self.rtt=0
            """

        self.qDelay=self.stt-self.minStt
        self.qDelayHistory.append(self.qDelay)
        self.qDelayHistory=self.qDelayHistory[-self.qHistorySize:]
        self.qRef=2*(self.errStt-self.minStt)/4
        self.refStt=self.minStt+self.qRef

        try:
            lastData=data['sent_data']
            self.totalDataSent=lastData['O_DATA_COUNTER']
            dataPacketsSent=lastData['O_PKG_COUNTER']-lastData['O_ACK_COUNTER']
            isIdle=self.u-dataPacketsSent
            self.lastIdlePacket=isIdle
            self.idlePackets.append(isIdle)
            self.idlePackets=self.idlePackets[-self.idleHistorySize:]
            self.ackSent=lastData['O_ACK_DATA_COUNTER']*self.TsendRef
        except:
            self.totalDataSent=0
            self.ackSent=0


        try:
            self.ackRate = 1.0*sum(self.ackHistory)/(len(self.ackHistory)*self.Tsend)*1408
        except:
            self.ackRate=0

        self.ackRatioHistory.append(self.ackRate)
        self.ackRatioHistory=self.ackRatioHistory[-self.idleHistorySize:]

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

        self.umaxHistory.append(self.umax)
        self.umaxHistory=self.umaxHistory[-self.umaxHistorySize:]
        self.setU()

    def setU(self):
        nackedSends=self.lastNack-self.lastAckedSent
        self.actualU=self.umax-self.ackSent
        predictedConsumeBw=self.actualU*(time.time()-self.lastSentTime-self.lastSleepTime)
        self.difBw=nackedSends*1408-predictedConsumeBw

        ynl=self.qDelay*self.actualU
        yn=ynl+self.difBw
        if yn<0:
            yn=0
        yref=self.qRef*self.actualU
        self.controlBw=(1-self.k)*(yref-yn)
        self.u=self.controlBw + self.actualU*self.TsendRef
        if self.errorPhase:
            self.u=self.actualU*self.TsendRef
        self.u=self.u/1408
        if round(self.u)<=0:
            self.u=2

        self.Tsend=self.TsendRef*ceil(self.u)/self.u
        self.u=int(ceil(self.u))
        #print self.peers
        #print 'uuuuuuuuuuuu:',self.u
        #print 'tsenddddd:',self.Tsend
        #print 'bwwwwwwwwww:',int(self.u*1408/self.Tsend)
        #print 'reported bw:',self.lastBW
        #print '---------------------------'
        self.send_bw()

    def send_bw(self):
        # print "SET BW", int(self.u*1408/self.Tsend), int(self.Tsend*pow(10,6))
        bora.bws_set(int(self.u*1408/self.Tsend), int(self.Tsend*pow(10,6)) )
        if self.peers:
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
        temp['umax']=self.umax*8/1024
        temp['rtt']=self.rtt
        temp['stt']=self.stt
        temp['minStt']=self.minStt
        temp['minRtt']=self.minRtt
        temp['errStt']=self.errStt
        temp['errRtt']=self.errRtt
        temp['ackRate']=self.ackRate*8/1024
        temp['refStt']=self.refStt
        temp['qRef']=self.qRef
        temp['qDelay']=self.qDelay
        temp['errorP']=self.errorsPer
        temp['Tsend']=self.Tsend
        temp['difBw']=self.difBw
        temp['controlBW']=self.controlBw
        temp['actualU']=self.actualU*8/1024
        temp['lastBW']=self.lastBW*8/1024
        temp['ackSent']=self.ackSent*8/1024
        temp['idleStatus']=self.idle
        temp['calcMin']=self.calculatedmin
        temp['idleAck']=self.idleAck
        temp['idleSttStatus']=self.idleSttStatus
        temp['lastIdlePacket']=self.lastIdlePacket
        temp['wrongStt']=self.wrongStt
        self.count+=1
        self.stats.append(temp)
        if len(self.stats)>20:
            self.stats.pop(0)

    def getStats(self):
        ret=self.stats[:]
        self.stats=[]
        return ret

