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
from twisted.internet import task
import gtk
from pkg_resources import resource_string

class OverlayViz(object):
    def __init__(self):
        self.count=0
        self.peerCount={}

        self.loopingCall=task.LoopingCall(self.getNeighbours)
        self.overlays={}
        self.overlays[0]=SubOverlayViz(self,"Base")
        self.overlays[1]=SubOverlayViz(self,"Super")
        self.overlays[2]=SubOverlayViz(self,"Inter")
        self.showing=False

    def start(self,interface):
        self.interface=interface
        if not self.loopingCall.running:
            self.loopingCall.start(5)
        for ov in self.overlays.values():
            ov.start()
        self.showing=True

    def stop(self):
        if self.loopingCall.running:
            self.loopingCall.stop()
        for ov in self.overlays.values():
            ov.stop()
        self.showing=False

    def getNeighbours(self):
        self.interface.getNeighbours(self.makeStruct)

    def makeStruct(self,peers,overlays):
        for p in peers:
            if p not in self.peerCount.keys():
                self.peerCount[p]=self.count
                self.count +=1


        final={}
        for ov,values in overlays.items():
            final[ov]={}
            for k,v in values['neighs'].items():
                final[ov][self.peerCount[k]]=[]
                for p in v:
                    final[ov][self.peerCount[k]].append((self.peerCount[p[0]],int(1000*p[1])))

            if values['energy']:
                en=values['energy']
                text='system energy=%f'%(sum(en)/len(en))
                print text+' for overlay '+str(ov)
                self.overlays[ov].addText(text)


            for p,v in overlays[ov]['stats'].items():
                v.append(self.peerCount[p])

            self.overlays[ov].setStats(overlays[ov]['stats'])

            if final[ov]:
                self.overlays[ov].makeGraph(final[ov])
            else:
                self.overlays[ov].makeEmptyGraph()

    def pause(self,pause):
        if pause:
            if self.loopingCall.running:
                self.loopingCall.stop()
        else:
            if not self.loopingCall.running:
                self.loopingCall.start(5)
        for ov in self.overlays.values():
            ov.pause(pause)

    def destroy(self):
        for ov in self.overlays.values():
            ov.destroy()


class SubOverlayViz(object):
    def __init__(self,parent,name):
        self.parent=parent

        self.builder = gtk.Builder()
        self.builder.add_from_string(resource_string(__name__, 'graphGui.glade'))
        self.builder.connect_signals(self)

        self.image=self.builder.get_object('image')
        self.image.show()

        self.legendView=self.builder.get_object('legendView')

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('Node',renderer, text=0)
        column.set_visible(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,0)
        self.legendView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('IP',renderer, text=1)
        column.set_visible(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,1)
        self.legendView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('port',renderer, text=2)
        column.set_visible(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,2)
        self.legendView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('#swaps',renderer, text=3)
        column.set_visible(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,3)
        self.legendView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('last swap',renderer, text=4)
        column.set_visible(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,4)
        self.legendView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('#satelites',renderer, text=5)
        column.set_visible(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,5)
        self.legendView.append_column(column)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn('last satelite',renderer, text=6)
        column.set_visible(True)
        column.set_reorderable(True)
        column.set_clickable(True)
        column.connect('clicked',self.collumn_clicked,6)
        self.legendView.append_column(column)

        self.sorting=gtk.SORT_ASCENDING
        self.sortId=0

        self.legendView.show()
        self.legendWindow=self.builder.get_object('legendWindow')
        self.legendWindow.set_visible(False)

        self.window=self.builder.get_object('window')
        self.window.set_title('Network graph')

        self.window.connect('delete-event', self.on_delete_event)
        self.tview=self.builder.get_object('textview')
        self.tbuffer=gtk.TextBuffer()
        self.tview.set_buffer(self.tbuffer)
        self.tview.show()

        self.window.set_title(name)

    def collumn_clicked(self,collumn,id):
        sortId=self.legendView.get_model().get_sort_column_id()

        sorting=gtk.SORT_DESCENDING
        if sortId[0]!=id:
            self.legendView.get_model().set_sort_column_id(id,sorting)
        else:
            if sortId[1]==gtk.SORT_DESCENDING:
                sorting=gtk.SORT_ASCENDING
            self.legendView.get_model().set_sort_column_id(id,sorting)

        self.sortId=id
        self.sorting=sorting

    def start(self):
        self.window.show()


    def stop(self):
        self.window.hide()


    def setStats(self,stats):
        self.stats=stats


    def makeEmptyGraph(self):
        self.g=nx.Graph()

        self.drawPlot()
        self.updateLegend()

    def makeGraph(self,final):
        self.g=nx.Graph()
        for k,p in final.items():
            edges=self.g.edges()
            for v in p:
                if not (k,v[0]) in edges and not (v[0],k) in edges:
                    self.g.add_edge(k,v[0],len=v[1])

        unconnected=[p for p in final.keys() if p not in self.g.nodes()]
        for p in unconnected:
            self.g.add_node(p)

        self.drawPlot()
        self.updateLegend()

    def drawPlot(self):
        a=nx.to_agraph(self.g)
        self.g=nx.from_agraph(a)
        fig=plt.figure()
        nx.draw_graphviz(self.g,prog='neato')
        plt.savefig("path.png")

        self.image.set_from_file("path.png")

    def updateLegend(self):
        legendStore=gtk.ListStore(int,str,int,int,int,int,int)
        legendStore.set_sort_column_id(self.sortId,self.sorting)
        self.legendView.set_model(legendStore)
        swap=0
        lastSwap=0
        satelite=0
        lastSatelite=0

        for p,c in self.stats.items():
            swap=c[0]
            lastSwap=int(c[1])
            satelite=c[2]
            lastSatelite=int(c[3])


            legendStore.append((c[4],p[0],p[1],swap,lastSwap,satelite,lastSatelite))

    def on_infoButton_toggled(self,widget):
        self.legendWindow.set_visible(widget.get_active())
        self.window.resize(1,1)

    def on_pauseButton_clicked(self,widget):
        if widget.get_stock_id()=='gtk-media-pause':
            pause=True
        else:
            pause=False
        self.parent.pause(pause)

    def pause(self,pause):
        widget=self.builder.get_object('pauseButton')
        if pause:
            widget.set_stock_id('gtk-media-play')
        else:
            widget.set_stock_id('gtk-media-pause')



    def addText(self,text):
        text +='\n'
        self.tbuffer.insert(self.tbuffer.get_end_iter(),text)
        self.tview.scroll_to_mark(self.tbuffer.get_insert(),0)


    def on_delete_event(self,*args):
        self.stop()
        return True
