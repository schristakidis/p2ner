# from matplotlib import pyplot as plt
from matplotlib import figure
import pygtk
pygtk.require("2.0")
import gtk
try:
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
except:
    pass
from twisted.internet import reactor
import numpy as np
from twisted.internet import task
from cPickle import loads
from twisted.web.xmlrpc import Proxy
import os,os.path
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
from matplotlib.font_manager import FontProperties
fontP = FontProperties()
fontP.set_size('small')
import csv
from p2ner.abstract.ui import UI


class PlotFig(object):
    def __init__(self,name,plots,x,shared=None):
        self.name=name
        self.plots=plots
        self.xType=x

        self.values={}
        # for p in self.plots:
        #     self.values[p] = [0 for x in range(300)]
        self.shared=shared
        self.pause=False
        self.draw=True
        self.line={}
        self.hidingPlots=[]
        self.initPlot()

    def initPlot(self):
        xAchse=np.arange(0,300,1)
        yAchse=np.array([0]*300)

        # fig=plt.figure()
        fig=figure.Figure()
        self.canvas=FigureCanvas(fig)
        self.fig=fig
        if not self.shared:
            self.ax = fig.add_subplot(111)
        else:
            self.ax=fig.add_subplot(111,sharex=self.shared)
        self.ax.grid(True)
        self.ax.set_title(self.name)
        self.ax.axis([0,300,-1.5,1.5])
        for p in self.plots:
            self.line[p],=self.ax.plot(xAchse,yAchse,'-',label=p[2])

        handles1, labels1 = self.ax.get_legend_handles_labels()
        self.ax.legend(handles1, labels1, prop = fontP, loc=2)

    def removePlot(self,plot):
        plot=[p for p in self.plots if p[2]==plot][0]
        self.ax.lines.remove(self.line[plot])
        self.hidingPlots.append(plot)
        if self.pause:
            self.updateYAxis()

    def addPlot(self,plot):
        plot=[p for p in self.plots if p[2]==plot][0]
        self.ax.lines.append(self.line[plot])
        self.hidingPlots.remove(plot)
        if self.pause:
            self.updateYAxis()

    def updateYAxis(self):
        miny=[]
        maxy=[]
        for p in self.plots:
            if p not in self.hidingPlots:
                miny.append(min(self.values[p]['y'][-300:]))
                maxy.append(max(self.values[p]['x'][-300:]))
        try:
            miny=min(miny)
            maxy=max(maxy)
            self.ax.set_ylim(miny-0.1*miny,maxy+0.1*maxy)
        except:
            pass
        self.fig.canvas.draw()

    def reloadPlot(self):
        self.RealtimePloter(False)

    def updatePlot(self,data):
        maxX=max([(data[p][self.xType][-1],p) for p in self.plots])
        self.values={}
        self.values['x']=data[maxX[1]][self.xType]
        for p in self.plots:
            self.values[p]={}
            # self.values['x']=range(len(self.data[p]))
            self.values[p]['x']=data[p][self.xType]
            self.values[p]['y']=data[p]['y']
        if not self.pause:
            self.RealtimePloter(True)


    def RealtimePloter(self,sub=True):
        if sub:
            limit=-50
        else:
            limit=-len(self.values['x'])
        CurrentXAxis=self.values['x']
        miny=[]
        maxy=[]
        for p in self.plots:
            CurrentXAxis2=self.values[p]['x']
            self.line[p].set_data(CurrentXAxis2,np.array(self.values[p]['y']))
            if p not in self.hidingPlots:
                miny.append(min(self.values[p]['y'][limit:]))
                maxy.append(max(self.values[p]['y'][limit:]))


        try:
            miny=min(miny)
            maxy=max(maxy)
            self.ax.set_ylim(miny-0.1*miny,maxy+0.1*maxy)
        except:
            pass

        if not self.shared:
            # self.ax.set_xlim(CurrentXAxis.min(),CurrentXAxis.max())
            try:
                self.ax.set_xlim(min(CurrentXAxis[limit:]),max(CurrentXAxis[limit:]))
            except:
                pass


            # self.ax.axis([CurrentXAxis.min(),CurrentXAxis.max(),min(self.values),max(self.values)])
        # else:
            # self.ax.set_ylim(min(self.values),max(self.values))

        if not self.shared:
            self.fig.canvas.draw()


    def getCanvas(self):
        return self.canvas

    def getSharedAxe(self):
        return self.ax

    def setPause(self,pause):
        self.pause=pause


class PlotGui(UI):
    def initUI(self,pid,plots,sharedx,statCollector):
        self.pid=pid
        self.statCollector=statCollector
        self.plots=plots
        self.fig={}
        self.builder = gtk.Builder()
        self.data={}
        commonX=None
        for k,v in plots.items():
            x=v['x']
            if not commonX:
                commonX=x
            else:
                if x!=commonX:
                    sharedx=False
            for s in v['stats']:
                if s not in self.data:
                    self.data[s]={}
                    self.data[s]['y']=[]
                if x not in self.data[s]:
                    self.data[s][x]=[]


        path = os.path.dirname( os.path.realpath( __file__ ) )
        self.builder.add_from_file(os.path.join(path, 'plotGui.glade'))

        self.builder.connect_signals(self)
        self.ui=self.builder.get_object('ui')
        self.ui.connect('delete-event',self.on_ui_destroy)
        self.table=self.builder.get_object('table1')

        self.loopingCall=task.LoopingCall(self.updatePlots)
        self.count=0
        self.sharedx=sharedx

        if not self.statCollector:
            self.builder.get_object('allButton').set_sensitive(False)
            self.builder.get_object('pauseButton').set_sensitive(False)

        self.makePlots()
        self.showing=True
        self.ui.show_all()

    def makePlots(self):
        panel=self.builder.get_object('vPanel')
        for k,v in self.plots.items():
            b=gtk.CheckButton(v['name'])
            b.set_active(True)
            b.connect('toggled',self.on_checkbutton_toggled)
            panel.pack_start(b,False,False)
            for i in v['stats']:
                b=gtk.CheckButton(i[2])
                b.set_active(True)
                b.connect('toggled',self.on_subcheckbutton_toggled,v['name'])
                panel.pack_start(b,False,False)
            l=gtk.Label('------------------------')
            panel.pack_start(l,False,False)
            self.addPlot(v['name'],v['stats'],v['x'])



    def on_ui_destroy(self,widget,*args):
        self.parent.plotDestroyed(self.pid)

    def on_exitButton_clicked(self,widget):
        self.parent.plotDestroyed(self.pid)
        self.ui.destroy()

    def on_pauseButton_clicked(self,widget):
        if widget.get_label()=='Pause':
            self.pause=True
            widget.set_label('Restart')
        else:
            widget.set_label('Pause')
            self.pause=False

        for n,f in self.fig.items():
            f['fig'].setPause(self.pause)

    def on_reloadButton_clicked(self,widget):
        for n,f in self.fig.items():
            f['fig'].reloadPlot()

    def on_checkbutton_toggled(self,widget):
        name=widget.get_label()
        if widget.get_active():
            self.fig[name]['box'].show()
        else:
            self.fig[name]['box'].hide()

    def on_subcheckbutton_toggled(self,widget,parent):
        name=widget.get_label()
        if widget.get_active():
            self.fig[parent]['fig'].addPlot(name)
        else:
            self.fig[parent]['fig'].removePlot(name)


    def addPlot(self,name,plots,x):
        if self.fig:
            newfig=PlotFig(name,plots,x,self.sharedAxis)
        else:
            newfig=PlotFig(name,plots,x,None)
            if self.sharedx:
                self.sharedAxis=newfig.getSharedAxe()
            else:
                self.sharedAxis=None

        self.fig[name]={}
        self.fig[name]['fig']=newfig
        canvas=newfig.getCanvas()
        vbox=gtk.VBox()
        vbox.pack_start(canvas,True,True)
        toolbar=NavigationToolbar(canvas,self.ui)
        vbox.pack_start(toolbar,False,False)
        self.fig[name]['box']=vbox
        self.table.attach(vbox,0,1,self.count,self.count+1)
        self.count+=1
        self.ui.show_all()


    def updatePlots(self,data):
        # if not self.fig:
        #     return
        for k,values in data.items():
            for v in values:
                self.data[k]['y'].append(v[0])
                for x,pos in [('customX',1),('time',2),('lpb',3)]:
                    if x in self.data[k]:
                        self.data[k][x].append(v[pos])

        for n,f in self.fig.items():
            f['fig'].updatePlot(self.data)

    def changeToolbar(self):
        self.fig['rtt']['toolbar'].canvas=self.fig['bw']['fig'].getCanvas()

    def on_allButton_clicked(self,widget):
        req=[]
        for k,v in self.data.items():
            stat=[]
            stat.append(k)
            for x in (('customX','x'),('time','time'),('lpb','lpb')):
                if x[0] in v:
                    stat.append(x[1])
                    stat.append(self.data[k][x[0]][0])
                    break
            req.append(stat)
        if req:
            self.statCollector(req,self.getAllStats)
            self.builder.get_object('allButton').set_sensitive(False)

    def getAllStats(self,stats):
        data={}
        for k,values in stats.items():
            if not k in data:
                data[k]={}
                data[k]['y']=[]
                for x in ('customX','time','lpb'):
                    data[k][x]=[]
            for v in values:
                data[k]['y'].append(v[0])
                for x,pos in [('customX',1),('time',2),('lpb',3)]:
                    data[k][x].append(v[pos])

        for k,values in self.data.items():
            for v in values.keys():
                self.data[k][v]=data[k][v]+self.data[k][v]

        self.on_reloadButton_clicked(None)
        self.builder.get_object('allButton').set_sensitive(True)


