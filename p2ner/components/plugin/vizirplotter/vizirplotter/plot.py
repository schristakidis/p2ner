from matplotlib import pyplot as plt
import pygtk
pygtk.require("2.0")
import gtk
import numpy as np
try:
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
    from twisted.internet import reactor
except:
    pass
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


class PlotFig(object):
    def __init__(self,name,plots,data,shared=None):
        self.name=name
        self.plots=plots
        self.data=data

        self.values={}
        for p in self.plots:
            self.values[p] = [0 for x in range(300)]
        self.shared=shared
        self.pause=False
        self.draw=True
        self.line={}
        self.hidingPlots=[]
        self.initPlot()

    def initPlot(self):
        xAchse=np.arange(0,300,1)
        yAchse=np.array([0]*300)

        fig=plt.figure()
        self.fig=fig
        self.canvas=FigureCanvas(fig)
        if not self.shared:
            self.ax = fig.add_subplot(111)
        else:
            self.ax=fig.add_subplot(111,sharex=self.shared)
        self.ax.grid(True)
        self.ax.set_title(self.name)
        self.ax.axis([0,300,-1.5,1.5])
        for p in self.plots:
            self.line[p],=self.ax.plot(xAchse,yAchse,'-',label=p)

        handles1, labels1 = self.ax.get_legend_handles_labels()
        self.ax.legend(handles1, labels1, prop = fontP, loc=2)

    def removePlot(self,plot):
        self.ax.lines.remove(self.line[plot])
        self.hidingPlots.append(plot)
        if self.pause:
            self.updateYAxis()

    def addPlot(self,plot):
        self.ax.lines.append(self.line[plot])
        self.hidingPlots.remove(plot)
        if self.pause:
            self.updateYAxis()

    def updateYAxis(self):
        miny=[]
        maxy=[]
        for p in self.plots:
            if p not in self.hidingPlots:
                miny.append(min(self.values[p][-300:]))
                maxy.append(max(self.values[p][-300:]))
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
        self.data=data
        for p in self.plots:
            self.values['x']=range(len(self.data[p]))
            self.values[p]=self.data[p]
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
            self.line[p].set_data(CurrentXAxis,np.array(self.values[p]))
            if p not in self.hidingPlots:
                miny.append(min(self.values[p][limit:]))
                maxy.append(max(self.values[p][limit:]))

        try:
            miny=min(miny)
            maxy=max(maxy)
            self.ax.set_ylim(miny-0.1*miny,maxy+0.1*maxy)
        except:
            pass

        if not self.shared:
            # self.ax.set_xlim(CurrentXAxis.min(),CurrentXAxis.max())
            self.ax.set_xlim(min(CurrentXAxis[limit:]),max(CurrentXAxis[limit:]))


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

class PlotGui(object):
    def __init__(self,plots):
        self.plots=plots
        self.fig={}
        self.builder = gtk.Builder()

        path = os.path.dirname( os.path.realpath( __file__ ) )
        self.builder.add_from_file(os.path.join(path, 'plot.glade'))

        self.builder.connect_signals(self)
        self.ui=self.builder.get_object('ui')
        self.ui.connect('delete-event',self.on_ui_destroy)
        self.table=self.builder.get_object('table1')
        self.loopingCall=task.LoopingCall(self.updatePlots)
        self.count=0
        self.sharedx=None

        self.makePlots()
        self.showing=True
        self.ui.show_all()

    def makePlots(self):
        panel=self.builder.get_object('vPanel')
        for k,v in self.plots.items():
            b=gtk.CheckButton(k)
            b.set_active(True)
            b.connect('toggled',self.on_checkbutton_toggled)
            panel.pack_start(b,False,False)
            for i in v:
                b=gtk.CheckButton(i)
                b.set_active(True)
                b.connect('toggled',self.on_subcheckbutton_toggled,k)
                panel.pack_start(b,False,False)
            l=gtk.Label('------------------------')
            panel.pack_start(l,False,False)
            self.addPlot(k,v)



    def on_ui_destroy(self,widget,*args):
        self.ui.hide()
        self.showing=False
        return True

    def on_exitButton_clicked(self,widget):
        self.ui.hide()
        self.showing=False

    def on_pauseButton_clicked(self,widget):
        if widget.get_label()=='Pause':
            self.pause=True
            widget.set_label('Restart')
        else:
            widget.set_label('Pause')
            self.pause=False

        for n,f in self.fig.items():
            f['fig'].setPause(self.pause)
            # print 'name:',n

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
        # print parent,name
        if widget.get_active():
            self.fig[parent]['fig'].addPlot(name)
        else:
            self.fig[parent]['fig'].removePlot(name)


    def addPlot(self,name,plots):
        # print 'adding:',name,plots
        if self.fig:
            newfig=PlotFig(name,plots,None,self.sharedx)
        else:
            newfig=PlotFig(name,plots,None,None)
            self.sharedx=newfig.getSharedAxe()

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
        for n,f in self.fig.items():
            f['fig'].updatePlot(data[n])

    def changeToolbar(self):
        self.fig['rtt']['toolbar'].canvas=self.fig['bw']['fig'].getCanvas()

    def ui_destroy(self):
        self.ui.destroy()

    def ui_hide(self):
        self.ui.hide()
        self.showing=False

    def ui_show(self):
        self.ui.show_all()
        self.showing=True
