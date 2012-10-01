# -*- coding: utf-8 -*-


#TODO: CHECK    normalizeTokens
def normalizeTokens(self, neighlist):
    if not len(neighlist):
        return
    numpeers = len(neighlist)
    probsum = 0.0
    for buf in neighlist:
        probsum += self.bufferList[buf].probability
    for buf in neighlist:
        buffer = self.bufferList[buf]
        buffer.probability = buffer.probability/probsum
        #print "probability: %f" % buffer.probability

#TODO: CHECK    getMostDeprived    
def getMostDeprived(self):
    '''Return the most deprived Buffer'''
    bl = [b for b in self.bufferList.values() if self.bufferList[x]]
    if len(bl) == 0:
        return None
    bl.sort(key=lambda x:x.fillLevel())
    d = bl[0]
    return d
        
def getMostDeprivedReq(bufferlist, myBuffer):
    buflist = bufferlist.keys()
    if len(buflist) == 0:
        return None
    bl = []
    for b in buflist:
        if len(b.request):
            bl.append(b)
    if len(bl) == 0:
        return None
    bl.sort(key=lambda x:x.getRelativeDeprivacy(myBuffer.getTrueBIDList()))
    d = bl[-1]
    return bufferlist[d]

#TODO: CHECK   getNDeprived         
def getNDeprived(self, n):
    '''Return the Nth most deprived Buffer'''
    bl = [b for b in self.bufferList.values() if self.bufferList[x]]
    if len(bl) == 0:
        return None
    bl.sort(key=lambda b:b.fillLevel())
    d = bl[n]
    return d

#TODO: CHECK    getMatching
def getMatching(self,buf):
    bl = [b for b in self.bufferList.values() if self.bufferList[x]]
    if len(bl)==0:
        return None
        
    mt=[]
    for x in bl:
        temp = bl.bIDListCompTrue(buf.getFalseBIDList())
        mt.append(temp)
        
    reqList=[]
    reqBlock=[]
        
    for i in range(len(mt)):
        found=-1
        reqBlock.append(-1)
        for j in mt[i]:
            if j not in reqList:
                found=j
            
        if found>=0:
            reqList.append(found)
            reqBlock[i]=found
        else:
            l=0
            fPlace=-1
            while l<i and fPlace==-1:
                for j in mt[i]:
                    if j==reqBlock[l]:
                        for k in mt[l]:
                            if k!=reqBlock[l] and k  not in reqList:
                                fPlace=k
                            
                        if fPlace>=0:
                            reqList.append[fPlace]
                            reqBlock[l]=fPlace
                            reqBlock[i]=j
                    
                l+=1
        
    for i in bl:
        i.req=reqBlock[i]
    return 
        
        

