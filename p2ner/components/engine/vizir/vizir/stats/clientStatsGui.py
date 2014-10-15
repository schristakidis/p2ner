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

class clientStatsGui(statsGui.statsGui):
    def initUI(self):
        self.makingNewGraph=False
        self.statinGraph=False
        self.liveMode=True
        self.localdb=None
        self.remote=False
        self.plots={}
        self.pid=0
        self.showing=True

        self.getStatKeys()
        self.ui=None


    def getStatKeys(self):
        self.interface.getVizirStatistics(self._getStatKeys)

    def _getStatKeys(self,stats):
        self.statKeys=loads(stats)
        if not self.ui:
            self.constructUI()



    def makeLiveGraph(self,stats,sharedx):
        newPlot= PlotGui(self.pid,deepcopy(self.newGraph),sharedx,self.getStats,_parent=self)
        self.plots[self.pid]=newPlot
        self.parent.statsController.subscribe([self.parent],stats,newPlot,newPlot.updatePlots)
        self.pid+=1

    def getStats(self,stats,func):
        self.statsController.getStats(self.parent,stats,func)

    def plotDestroyed(self,plot):
        if plot not in self.plots:
            return
        if not type(self.plots[plot])==dict:
            self.statsController.unsubscribe(self.plots[plot])
        del self.plots[plot]


    def on_loadButton_clicked(self,widget,data=None):
        print 'not available in vizir'





if __name__=='__main__':
    statsGui()
    reactor.run()



