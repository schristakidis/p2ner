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

import networkx as nx
import matplotlib.pyplot as plt
import pylab
from twisted.internet import task


class OverlayViz(object):
    def __init__(self):
        pylab.ion()
        self.fig=None
        self.loopingCall=task.LoopingCall(self.getNeighbours)
        
    def start(self,interface):
        self.interface=interface
        if not self.loopingCall.running:
            self.loopingCall.start(5)
        
    def stop(self):
        if self.loopingCall.running:
            self.loopingCall.stop()
            if self.fig:
                pylab.close(self.fig)
            
    def getNeighbours(self):
        self.interface.getNeighbours(self.makeStruct)
        
    def makeStruct(self,neighs):
        count=0
        peer={}
        for k,v in neighs.items():
            if k not in peer.keys():
                peer[k]=count
                count +=1
            for p in v:
                if p[0] not in peer.keys():
                    peer[p[0]]=count
                    count +=1
                    
        self.final={}
        for k,v in neighs.items():
            self.final[peer[k]]=[]
            for p in v:
                self.final[peer[k]].append((peer[p[0]],int(1000*p[1])))
        
        if self.final:        
            self.makeGraph()
        
    def makeGraph(self):
        self.g=nx.Graph()
        for k,p in self.final.items():
            edges=self.g.edges()
            for v in p:
                if not (k,v[0]) in edges and not (v[0],k) in edges:
                    self.g.add_edge(k,v[0],len=v[1])
                    
        unconnected=[p for p in self.final.keys() if p not in self.g.nodes()]
        for p in unconnected:
            self.g.add_node(p)
            
        #if len(self.final)==1:
        #    self.g.add_node(0) 
        
        self.drawPlot()
        
    def drawPlot(self):
        a=nx.to_agraph(self.g)
        self.g=nx.from_agraph(a)
        if self.fig:
            pylab.close(self.fig)
        self.fig=pylab.figure()
        pylab.show()
        nx.draw_graphviz(self.g,prog='neato')
        self.fig.canvas.draw()
        pylab.draw()
        
