      
#from twisted.internet import gtk2reactor
#gtk2reactor.install()
import matplotlib
matplotlib.use('GTKAgg')
#import numpy as np
#from matplotlib.lines import Line2D
#from pylab import *
import pygtk
pygtk.require("2.0")
import gtk
import time
import os,sys
from twisted.internet import reactor,task
#import matplotlib.numerix as nx
from bisect import bisect
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg
from matplotlib.figure import Figure 
#import gobject
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
#from scipy import interpolate
from pylab import setp
from p2ner.util.utilities import get_user_data_dir

class PlotGui(object):
    def get_bg_bbox(self):
        return self.ax.bbox.padded(-3)
       
    def __init__(self,stats,interface=None,file=None,combine=False):
        
        if len(stats)==1:
            combine=True
        self.interface=interface
        self.file=file
        self.combine=combine
    
        path = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'plot.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'plot.glade'))
            
        self.builder.connect_signals(self)
            
        self.ui=self.builder.get_object('ui')
        self.pbox=self.builder.get_object('pbox')
        self.nbox=self.builder.get_object('nbox')
        self.figure = Figure()
        self.canvas = FigureCanvasGTKAgg(self.figure)
        self.canvas.set_size_request(600, 400)
        if combine:
            self.ax = self.figure.add_subplot(111)
            self.ax.grid(b=True,which='both')
        
        self.stats={}
        c=0
        size=0.2+0.025*(len(stats)-1)
        step=(1-size)/len(stats)
        for s,sc in stats:
            self.stats[s]={}
            self.stats[s]['scale']=sc
            self.stats[s]['x']=[]
            self.stats[s]['y']=[]
            self.stats[s]['count']=0
            if not self.combine:
                if c==0:
                    ax=self.figure.add_axes([0.1, 0.1, 0.8, step])
                    self.ax=ax
                    self.ax.grid(b=True,which='both')
                else:
                    ax=self.figure.add_axes([0.1,0.1+c*(0.025+ step), 0.8, step],sharex=ax) 
                    ax.grid(b=True,which='both')
                    setp(ax.get_xticklabels(), visible=False)
                self.stats[s]['ax']=ax
                ax.set_ylabel(s)
                self.stats[s]['line'],=ax.plot([],[],label=s)
                #ax.legend()
            else:
                self.stats[s]['line'],=self.ax.plot([],[],label=s)
           
            c+=1
        
        if self.combine:
            self.ax.legend(loc=(0.,1.) ,mode="expand",borderaxespad=0. ,ncol=len(self.stats))
            
        self.xwidth=30
        self.t0=-1
        
        self.ax.set_xlim(0, self.xwidth)
        
    
        self.pbox.pack_start(self.canvas,True,True)
        
        self.navToolbar = NavigationToolbar(self.canvas, self.ui)
        self.nbox.pack_start(self.navToolbar)
        self.nbox.hide()
        
        self.canvas.show()
        self.pbox.show()
        self.ui.show()
        
       
        if not self.file:
            self.loop=task.LoopingCall(self.getValues)
            self.loop.start(1)
        else:
            self.nbox.show()
            self.builder.get_object('pauseButton').set_sensitive(False)
            self.builder.get_object('saveButton').set_sensitive(False)
            self.readFiles()

    def on_pauseButton_clicked(self,widget):
        if widget.get_label()=='Pause':
            widget.set_label('Resume')
            self.nbox.show()
            self.loop.stop()
            self.update(True)
        else:
            widget.set_label('Pause')
            self.nbox.hide()
            self.loop.start(1)
    
    def on_closeButton_clicked(self,widget):
        try:
            self.loop.stop()
        except:
            pass
        self.ui.destroy()
    
    def on_ui_destroy(self,widget=None,data=None):
        try:
            self.loop.stop()
        except:
            pass
        
    def update(self,static=False):
        try:
            tlast=max([s['x'][-1] for s in self.stats.values()])
        except:
            return
        if not static:
            t0 = tlast  - self.xwidth
            if t0 < 0:
                t0 = 0
        else:
            t0=0
            
        for s in self.stats:
            st=self.stats[s]
            i = bisect(st['x'], t0)
            if i>0:
                i=i-1
            
            toleft=st['x'][i]
            st['newx']=st['x'][i:]
            st['newy']=st['y'][i:]
            try:
                st['maxy']=max(st['newy'][1:])
            except:
                 st['maxy']=max(st['newy'])
                   
            if not self.combine:
                limnow=st['ax'].get_ylim()[1]
                if abs(st['maxy']-limnow) > st['maxy']/2 or st['maxy']>limnow:
                    st['ax'].set_ylim(-0.1, st['maxy']*1.2)
            
        self.ax.set_xlim(t0, tlast)
        
        if self.combine:
            ylim=max([s['maxy'] for s in self.stats.values()])
    
            limnow = self.ax.get_ylim()[1]
            if abs(ylim-limnow) > ylim/2 or ylim>limnow:
                self.ax.set_ylim(-0.1, ylim*1.2)
        
        for s in self.stats.values():
            s['line'].set_data(s['newx'],s['newy'])
        
        self.ax.figure.canvas.draw_idle()
        
    def getValues(self):
        self.interface.getStatValues(self.getStatValues,[(k,v['count']) for k,v in self.stats.items()])
        
    def getStatValues(self,stats):
        update=False
        if self.t0<0:
            m=[v[1][0][1] for v in stats if v[1]]
            if m:
                self.t0=min(m)
               
        for s,v,c in stats:
            #for b,t in v:
            #   print b,t
            if not len(v):
                break
            
            st=self.stats[s]
            update=True
            x=[x[1]-self.t0 for x in v]
            y=[y[0]*st['scale'] for y in v]
            st['x']=st['x']+x
            st['y']=st['y']+y
            st['count']=c
            
            
        if update:
            self.update()

    def on_saveButton_clicked(self,widget):
        if self.loop.running:
            self.on_pauseButton_clicked(self.builder.get_object('pauseButton'))
        self.builder.get_object('buttonBox').set_visible(False)
        self.builder.get_object('saveBox').set_visible(True)
    
    def on_cButton_clicked(self,widget=None):
        self.builder.get_object('buttonBox').set_visible(True)
        self.builder.get_object('saveBox').set_visible(False)
        
    def on_sButton_clicked(self,widget):
        en=self.builder.get_object('fileEntry').get_text()
        if not en:
            return
        
        file=os.path.join(get_user_data_dir(),'stats')
        if not os.path.isdir(file):
            os.mkdir(file)
            
        en1=en+'.stat'    
        f=open(os.path.join(file,en1),'w')
        for s,v in self.stats.items():
            f.write(s+'\n')
            en2=en+s
            f2=open(os.path.join(file,en2),'w')
            for i in range(len(v['x'])):
                line=str(v['x'][i])+','+str(v['y'][i]/v['scale'])+'\n'
                f2.write(line)
            f2.close()
        f.close()
        self.on_cButton_clicked()
        
    def readFiles(self):
        en=self.file[:-5]
        dir=os.path.dirname(self.file)
        for s,v in self.stats.items():
            en1=en+s
            en1=os.path.join(dir,en1)
            en1=en1.rsplit()[0]
            f=open(en1,'r')
            for line in f.readlines():
                x,y=line.split(',')
                v['y'].append(float(y)*v['scale'])
                v['x'].append(float(x))
            f.close()
        self.update(True)
                
            
        
        
        
