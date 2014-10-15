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

import os, sys
from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except:
    pass
from twisted.internet import reactor
import pygtk
pygtk.require("2.0")
import gtk
from gtkgui.remotefilechooser import RemoteFileChooser
from p2ner.util.utilities import get_user_data_dir
from gtkgui.plot import PlotGui
from pkg_resources import resource_string
from p2ner.abstract.ui import UI
from gtkgui.plotGui import PlotGui
from copy import deepcopy
from gtkgui.statsdb import DB
from cPickle import loads,dumps,load,dump
import gtkgui.statsGui as statsGui
from random import choice

class vizirStatsGui(statsGui.statsGui):
    def initUI(self):
        self.makingNewGraph=False
        self.statinGraph=False
        self.liveMode=True
        self.localdb=None
        self.remote=False
        self.plots={}
        self.pid=0
        self.showing=True
        self.ui=None

        self.getStatKeys()

    def constructMenu(self):
        return

    def getStatKeys(self):
        sid=self.parent.getProducingId()
        if sid:
            sid=sid[0][1]
        else:
            if not self.ui:
                self.constructUI()
            else:
                return

        peer = choice(self.parent.getRunningPeerObjects(sid))
        peer.interface.getVizirStatistics(self._getStatKeys)

    def _getStatKeys(self,stats):
        self.statKeys=loads(stats)
        if not self.ui:
            self.constructUI()


    def statSelected(self,treeview,path,col,model):
        if not self.makingNewGraph:
            return

        if not self.statinGraph:
            self.statinGraph=True

        compRow=self.componentTreeview.get_selection().get_selected_rows()[1][0]
        comp=self.componentTreeview.get_model()[compRow][0]

        idRow=self.sidTreeview.get_selection().get_selected_rows()[1][0]
        sid=self.sidTreeview.get_model()[idRow][0]

        stat=model[path][0]

        if (comp,sid,stat) in self.newSubGraph:
            return
        self.newSubGraph.append((comp,sid,stat))
        self.lStore.append((stat,))
        self.on_sub_clicked(None)

    def on_sub_clicked(self,widget):
        super(vizirStatsGui,self).on_sub_clicked(widget)
        self.newGraph[self.subCount]['x'].remove_text(0)



    def makeLiveGraph(self,stats,sharedx):
        graph=deepcopy(self.newGraph)
        x=None
        for i,sub in graph.items():
            newStats=[]
            for line in sub['stats']:
                comp=line[0]
                sid=line[1]
                sname=line[2]
                for sufix in ('10','50','90','av'):
                    newStats.append((comp,sid,sname+sufix))
            graph[i]['stats']=newStats
            graph[i]['name']=sname
            if not x:
                x=sub['x']
            else:
                sub['x']=x

        newPlot= PlotGui(self.pid,graph,sharedx,self.getStats,_parent=self)
        self.plots[self.pid]=newPlot
        self.parent.statsController.subscribe(None,stats,newPlot,newPlot.updatePlots,x)
        self.pid+=1

    def getStats(self,stats,func):
        print 'not yet implemented for vizir system stats'

    def plotDestroyed(self,plot):
        if plot not in self.plots:
            return
        if not type(self.plots[plot])==dict:
            self.statsController.unsubscribe(self.plots[plot])
        del self.plots[plot]



