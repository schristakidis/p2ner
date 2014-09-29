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
from p2ner.core.statsFunctions import setValue

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
        self.sendEstimatedBWInterval=0.1
        self.stats=[]
        self.count=0
        self.errorsPer=0
        self.difBw=0
        self.controlBw=0
        self.actualU=0
        self.lastBW=0
        self.idleHistorySize=30    #the size in Tsend intervals for storring last Stts
        self.idleHistorySizeDuringNoErrors=20 # the last Tsend intervals when there are no errors
        self.recHistory=[]  # holds the lastSTTs for the peers

        self.qDelayErr=0.1
        self.ackSentHistory=[]
        self.ackSentHistorySize=10
        self.ackSent=0

        self.reportedU=self.u
        self.sendInterval=0
        self.delta=0
        self.errorThres=0

        self.calculatedmin=0
        self.idleSttStatus=0
        self.lastIdlePacket=0

        self.controlBwHistory=[]
        self.controlBwHistorySize=5
        # self.ackRatioHistory=[] # used in old check idle
        # self.idleAck=0
        # self.idle=0
        # self.idlePackets=[]

        #    #used for the check wrongStt algorithm
        # self.qHistorySize=10
        # self.qDelayHistory=[]
        # self.qDelayPerPeer=[]
        # self.wrongStt=0
        # self.wrongSttperPeer=0
        # self.wrongThres=0.005**2
        # self.secondNormPerPeer=0
        # self.forceIdle=False



    def start(self):
        reactor.callInThread(bws_thread, self, self.TsendRef)
        self.loopingCall.start(self.sendEstimatedBWInterval)

    def checkIdle(self):
        const=True
        self.idleSttStatus=0
        self.delta=1.0*1500/self.maxumax


        if self.errorPhase or self.recoveryPhase:
            recHistory=self.recHistory
        else:
            recHistory=self.recHistory[-self.idleHistorySizeDuringNoErrors:]
        temp={}
        for stt,p in recHistory:
            if p not in temp.keys():
               temp[p]=[]
            temp[p].append(stt)

        for p,v in temp.items():
            if not const:
                break
            lstt=v[0]
            for stt in v[1:]:
                if stt>self.delta+lstt or stt<lstt-self.delta:
                    const=False
                    break


        if const and len(self.recHistory)>10 and self.errorsPer<2:
            self.idleSttStatus=1
            for p in temp.keys():
                self.peers[p]['calcMin']=min(temp[p])
                self.peers[p]['calcMinTime']=time.time()
        else:
            self.idleSttStatus=0

        return

        # if const:
        #     # self.idleSttStatus=1
        #     try:
        #         first=self.ackRatioHistory[0]
        #         last=self.ackRatioHistory[-1]
        #         self.idleAck=1.0*(last-first)/last
        #     except:
        #         self.idleAck=0

        #     line=False
        #     if self.idleAck>0.1:
        #         a=1.0*(last-first)/len(self.ackRatioHistory)
        #         line=True
        #         for x in range(len(self.ackRatioHistory)):
        #             point1=0.9*first+a*x
        #             point2=1.1*first+a*x
        #             if self.ackRatioHistory[x]<point1 or self.ackRatioHistory[x]>point2:
        #                 line=False

        #     if line:
        #         idle=True
        #     else:
        #         isIdle=True
        #         for i in self.idlePackets:
        #             if i<=1:
        #                 isIdle=False
        #                 break
        #         if isIdle:
        #             idle=True

        #     if idle and not self.errorPhase:
        #         self.idle+=1
        #         if self.idle>2:
        #             # for p in temp.keys():
        #             #     self.peers[p]['calcMin']=min(temp[p])
        #             #     self.peers[p]['calcMinTime']=time.time()
        #             self.idle=2
        #             # if self.forceIdle:
        #             #     self.forceIdle=False
        #     else:
        #         self.idle=0
        # else:
        #     self.idle=0






    def update(self,data):
        ackSum=0
        errSum=0
        qDperPeer={}
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

            if peer['error_last']:
                self.qDelayErr=(peer['errSTT']-peer['minSTT'])*pow(10,-6)


            ackSum+=peer['acked_last']
            errSum+=peer['error_last']

            # try:
            #     qDperPeer[p]=self.peers[p]['lastStt']-self.peers[p]['calcMin']
            # except:
            #     pass


        # for p,d in qDperPeer.items():
        #     self.qDelayPerPeer.append((p,d))

        # self.qDelayPerPeer=self.qDelayPerPeer[-self.qHistorySize:]

        if not self.peers:
            self.send_bw()
            return

        self.ackHistory.append(ackSum)
        self.errorHistory.append(errSum)
        if len(self.ackHistory)>self.historySize:
            self.ackHistory=self.ackHistory[-self.historySize:]
            self.errorHistory=self.errorHistory[-self.historySize:]

        # self.checkMinStt(data)

        lastAck=data['last_ack']
        executeAlgo=True
        if lastAck:
            lastPeer=(lastAck['host'],lastAck['port'])
            self.recHistory.append((self.peers[lastPeer]['lastStt'],lastPeer))
            self.recHistory=self.recHistory[-self.idleHistorySize:]

            self.checkIdle()

            self.rtt=lastAck['RTT']*pow(10,-6)
            self.stt=lastAck['STT']*pow(10,-6)
            self.minRtt=self.peers[lastPeer]['minRtt']
            try:
                self.minStt=self.peers[lastPeer]['calcMin']
            except:
                self.minStt=self.peers[lastPeer]['minStt']

            #if lastStt is less than the calculated minimum update values
            if self.peers[lastPeer]['lastStt']<self.minStt:
                self.minStt=self.peers[lastPeer]['lastStt']
                self.peers[lastPeer]['calcMin']=self.minStt

            self.errRtt=self.peers[lastPeer]['errorRtt']
            # self.errStt=self.peers[lastPeer]['errorStt']
            self.errStt=self.minStt+self.qDelayErr


            errors=sum(self.errorHistory)
            acks=sum(self.ackHistory)
            # self.errorsPer=100.0*errors/acks
            self.errorsPer=errors

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
            # self.minRtt=0
            # self.minStt=0
            # self.errRtt=0
            # self.errStt=0
            # self.stt=0
            # self.rtt=0

        self.qDelay=self.stt-self.minStt

        # self.qDelayHistory.append(self.qDelay) #used for wrongStt algo
        # self.qDelayHistory=self.qDelayHistory[-self.qHistorySize:]

        # self.qRef=2*(self.errStt-self.minStt)/4 # old way to calculate qRef

        # set qref according to the link capacity
        if self.delta:
            self.qRef=-self.delta
        else:
            self.qRef=-0.005
        self.refStt=self.minStt+self.qRef

        # self.checkWrongStt()

        try:
            lastData=data['sent_data']
            # self.totalDataSent=lastData['O_DATA_COUNTER']
            dataPacketsSent=lastData['O_PKG_COUNTER']-lastData['O_ACK_COUNTER']
            isIdle=self.u-dataPacketsSent
            self.lastIdlePacket=isIdle
            # self.idlePackets.append(isIdle)
            # self.idlePackets=self.idlePackets[-self.idleHistorySize:]
            self.ackSent=(lastData['O_ACK_DATA_COUNTER']+20*lastData['O_ACK_COUNTER'])/self.TsendRef
            self.ackSentHistory.append(self.ackSent)
            self.ackSentHistory=self.ackSentHistory[-self.ackSentHistorySize:]
            self.ackSent=1.0*sum(self.ackSentHistory)/len(self.ackSentHistory)
        except :
            # self.totalDataSent=0
            self.ackSent=0


        try:
            self.ackRate = 1.0*sum(self.ackHistory)/(len(self.ackHistory)*self.Tsend)*1408
        except:
            self.ackRate=0

        # self.ackRatioHistory.append(self.ackRate)    #used in old check idle
        # self.ackRatioHistory=self.ackRatioHistory[-self.idleHistorySize:]

        if executeAlgo:
            self.setUmax()
        else:
            self.send_bw()

    def setUmax(self):
        bw=bora.get_bw_msg()
        if not bw:
            self.bwHistory.append(-1)
        else:
            for b in bw:
                self.bwHistory.append(b['bw'])

        self.bwHistory=self.bwHistory[-self.bwHistorySize:]

        posBwHistory=[]
        if self.bwHistory:
            posBwHistory=[b for b in self.bwHistory if b>0]

        if not posBwHistory:
            self.send_bw()
            return

        tcpTestbed=False

        tumax = sorted(self.bwHistory)
        if not tcpTestbed:
            try:
                self.umax = tumax[-3]
            except:
                self.umax = tumax[0]
        else:
            #just for testing with tcp testbed
            self.umax=min([b for b in self.bwHistory if b>0])


        if self.umax<1:
            self.umax=self.maxumax

        self.lastBW = self.bwHistory[-1]
        self.maxumax=self.umax
        self.errorThres=sum(self.controlBwHistory)

        if not self.errorPhase and (self.errorThres>2*self.controlBwHistorySize or self.errorsPer>4):
            self.errorPhase=True
            self.recoveryPhase=False

        if self.errorPhase:
            self.umax=self.umax/2
            self.prevumax=self.maxumax/30

        if self.errorPhase  and self.errorThres<2*self.controlBwHistorySize and self.errorsPer<2:
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

        ynl=self.qDelay*self.actualU
        yn=ynl+self.difBw
        if yn<0:
            yn=0
        yref=self.qRef*self.actualU
        self.controlBw=(1-self.k)*(yref-yn)
        self.controlBwHistory.append(-self.controlBw/1408.0)
        self.controlBwHistory=self.controlBwHistory[-self.controlBwHistorySize:]
        self.u=self.controlBw + self.actualU*self.TsendRef
        if self.errorPhase:
            self.u=self.actualU*self.TsendRef
        self.u=self.u/1408
        if round(self.u)<=3:
            self.u=3

        self.Tsend=self.TsendRef*ceil(self.u)/self.u
        self.u=int(ceil(self.u))
        self.send_bw()

    def send_bw(self):
        u=self.u
        self.reportedU=u
        self.sendInterval=self.Tsend/u
        bora.bws_set(int(u*1408/self.Tsend), int(self.Tsend*pow(10,6)))
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
        setValue(self,'u',self.u,True)
        temp['umax']=self.umax*8/1024
        setValue(self,'umax',self.umax*8/1024,True)
        temp['rtt']=self.rtt
        temp['stt']=self.stt
        setValue(self,'stt',self.stt,True)
        setValue(self,'rtt',self.rtt,True)
        temp['minStt']=self.minStt
        setValue(self,'minStt',self.minStt,True)
        temp['minRtt']=self.minRtt
        setValue(self,'minRtt',self.minRtt,True)
        temp['errStt']=self.errStt
        setValue(self,'errStt',self.errStt,True)
        temp['errRtt']=self.errRtt
        setValue(self,'errRtt',self.errRtt,True)
        temp['ackRate']=self.ackRate*8/1024
        setValue(self,'ackRate',self.ackRate*8/1024,True)
        temp['refStt']=self.refStt
        setValue(self,'refStt',self.refStt,True)
        temp['qRef']=self.qRef
        setValue(self,'qRef',self.qRef,True)
        temp['qDelay']=self.qDelay
        setValue(self,'qDelay',self.qDelay,True)
        temp['errorP']=self.errorsPer
        setValue(self,'errorP',self.errorsPer,True)
        temp['Tsend']=self.Tsend
        setValue(self,'Tsend',self.Tsend,True)
        temp['difBw']=self.difBw
        setValue(self,'difBw',self.difBw,True)
        temp['controlBW']=self.controlBw
        setValue(self,'controlBW',self.controlBw,True)
        temp['actualU']=self.actualU*8/1024
        setValue(self,'actualU',self.actualU*8/1024,True)
        temp['lastBW']=self.lastBW*8/1024
        setValue(self,'lastBW',self.lastBW*8/1024,True)
        temp['ackSent']=self.ackSent*8/1024
        setValue(self,'ackSent',self.ackSent*8/1024,True)
        # temp['idleStatus']=self.idle
        # setValue(self,'idleStatus',self.idle,True)
        temp['calcMin']=self.calculatedmin
        setValue(self,'calcMin',self.calculatedmin,True)
        # temp['idleAck']=self.idleAck
        # setValue(self,'idleAck',self.idleAck,True)
        temp['idleSttStatus']=self.idleSttStatus
        setValue(self,'idleSttStatus',self.idleSttStatus,True)
        temp['lastIdlePacket']=self.lastIdlePacket
        setValue(self,'lastIdlePacket',self.lastIdlePacket,True)
        # temp['wrongStt']=self.wrongSttperPeer
        # setValue(self,'wrongStt',self.wrongSttperPeer,True)
        temp['errorThres']=self.errorThres
        setValue(self,'errorThres',self.errorThres,True)
        # temp['secondNormPerPeer']=self.secondNormPerPeer
        # setValue(self,'secondNormPerPeer',self.secondNormPerPeer,True)
        temp['delta']=self.delta
        setValue(self,'delta',self.delta,True)
        temp['sendInterval']=self.sendInterval
        setValue(self,'sendInterval',self.sendInterval,True)
        self.count+=1
        self.stats.append(temp)
        if len(self.stats)>20:
            self.stats.pop(0)

    def getStats(self):
        ret=self.stats[:]
        self.stats=[]
        return ret

    def getReportedBW(self):
        return self.reportedU



    # def checkMinStt(self,data):
    #     shouldCalculateMin=[]
    #     for peer in data['peer_stats']:
    #         p=(peer["host"],peer["port"])
    #         if not 'calcMin' in self.peers[p].keys():
    #             if not 'waitingMin' in self.peers[p].keys():
    #                 self.peers[p]['waitingMin']=0

    #             if not self.peers[p]['waitingMin']:
    #                 shouldCalculateMin.append(p)
    #             else:
    #                 self.peers[p]['waitingMin']-=1

    #     goodPeer=None
    #     if shouldCalculateMin:
    #         try:
    #             goodPeer=max([(v['calcMinTime'],p) for p,v in self.peers.items() if 'calcMin' in v.keys()])[1]
    #         except:
    #             pass

    #     if goodPeer:
    #         for p in shouldCalculateMin:
    #             self.peers[p]['waitingMin']=10
    #             d=deferToThread(bora.send_cookie,goodPeer[0],goodPeer[1],p[0],p[1])
    #             d.addCallback(self.updateMin,goodPeer,p)

    # def updateMin(self,data,goodPeer,peer):
    #     if not data:
    #         return
    #     print 'update minnnnnnnnnnnnn'
    #     print 'goodPeer:',goodPeer
    #     print 'peer:',peer
    #     print data
    #     for line in data:
    #         if line['host']==goodPeer[0] and line['port']==goodPeer[1]:
    #             goodStt=line['STT']*pow(10,-6)
    #         elif line['host']==peer[0] and line['port']==peer[1]:
    #             stt=line['STT']*pow(10,-6)
    #         else:
    #             print 'error in update minnnnnnnnnnnn'
    #             return

    #     delay=goodStt-self.peers[goodPeer]['calcMin']
    #     self.peers[peer]['calcMin']=stt-delay
    #     self.peers[peer]['waitingMin']=0



    # def checkWrongStt(self):
    #     self.wrongStt=0
    #     if not self.qDelayHistory or self.forceIdle:
    #         self.wrongSttperPeer=0
    #         return

    #     temp={}
    #     for d in self.qDelayPerPeer:
    #         if not d[0] in temp.keys():
    #             temp[d[0]]=[]
    #         temp[d[0]].append(d[1])

    #     if len(temp.keys())<2:
    #         self.wrongSttperPeer=0
    #         return

    #     cont=True
    #     for dPeer in temp.values():
    #         avg=sum(dPeer)/len(dPeer)
    #         second=sum([(d-avg)**2 for d in dPeer])/len(dPeer)
    #         if second>self.wrongThres:
    #             cont=False

    #     if not cont:
    #         self.wrongSttperPeer=0
    #         self.secondNormPerPeer=0
    #         return

    #     delays=[sum(d)/len(d) for d in temp.values()]
    #     avgDelay=sum(delays)/len(delays)
    #     self.secondNormPerPeer=sum([(d-avgDelay)**2 for d in delays])/len(delays)
    #     if self.secondNormPerPeer>self.wrongThres:
    #         self.wrongSttperPeer+=1
    #         if self.wrongSttperPeer>2:
    #             self.wrongSttperPeer=2
    #             # self.shouldForceIdle()


    # def shouldForceIdle(self):
    #     self.forceIdle=True
    #     for p in self.peers:
    #         try:
    #             self.peers[p].pop('calcMin')
    #             self.peers[p].pop('calcMinTime')
    #         except:
    #             pass
    #     print 'should force idle'
