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
import gobject
from serversGui import serversGUI
from producerGui import ProducerGui
from time import strftime,localtime
from twisted.web.xmlrpc import Proxy
from logger.loggerGui import Logger
from options.options import optionsGui
from console import start_console
from p2ner.core.namespace import Namespace, initNS
from p2ner.abstract.ui import UI
from statsGui import statsGui
from versioncheck import getVersion as checkVersion
from measureupload import MeasureUpload
from networkGui import NetworkGui
from p2ner.core.components import loadComponent
from chatClientUI import ChatClient
from pkg_resources import resource_string
from p2ner.core.preferences import Preferences 

streamListStore=[('streamID',int),('ip',str),('port',int),('title',str),('author',str),('type',str),('live',bool),('startTime',str),('startable',bool),('republish',bool),('password',bool),('subscribed',bool)]

class clientGui(UI):

	def initUI(self,remote=True):
		self.remote=remote
		if remote:
			from interface.xml.xmlinterface import Interface
			from interface.xml.connectgui import ConnectGui
			ConnectGui(self)
			self.interface=Interface(_parent=self)
			#self.logger=Logger(self)
			self.logger=Logger(self)
		else:
			#from interface.localinterface import Interface
			#self.interface=Interface(_parent=self)
			self.interface=self.root.interface
			self.logger=Logger(self)
			self.rProducerViewer=None
			reactor.callLater(0,self.startUI)
	
	def loadPreferences(self):
		self.preferences=Preferences(remote=True,func=self.startUI,_parent=self)
		self.preferences.start()
		
	def startUI(self):
		self.lastSelectedId=None
		self.lastSelectedType=None
		self.streams={}
		self.knownStreams={}
		path = os.path.realpath(os.path.dirname(sys.argv[0])) 
		self.builder = gtk.Builder()
		"""
		try:
			self.builder.add_from_file(os.path.join(path,'clientall.glade'))
		except:
			path = os.path.dirname( os.path.realpath( __file__ ) )
			self.builder.add_from_file(os.path.join(path, 'clientall.glade'))
		"""
		self.builder.add_from_string(resource_string(__name__, 'clientall.glade'))
		self.builder.connect_signals(self)
		
		self.serversButtonClicked=False
		
		self.createMenu()
		self.options=optionsGui(_parent=self)#self,self.visibleCollumns)

		self.streamsTreeview = self.builder.get_object("streamsTreeview")
		self.streamsModel=gtk.ListStore(*[typ[1] for typ in streamListStore])
		self.streamsTreeview.set_model(self.streamsModel)
		

		self.subTreeview = self.builder.get_object("subTreeview")
		self.subModel = self.streamsModel.filter_new(root=None)
		self.subTreeview.set_model(self.subModel)
		#self.subTreeview.set_headers_visible(False)

		self.publishTreeview=self.builder.get_object('publishTreeview')
		self.publishModel=gtk.ListStore(*[typ[1] for typ in streamListStore])
		self.publishTreeview.set_model(self.publishModel)
		
		for i in range(len(streamListStore)):
			renderer=gtk.CellRendererText()
			column=gtk.TreeViewColumn(streamListStore[i][0],renderer, text=i)
			column.set_resizable(True)
			column.set_visible(False) #vis[i]
			self.streamsTreeview.append_column(column)

			renderer=gtk.CellRendererText()
			column=gtk.TreeViewColumn(streamListStore[i][0],renderer, text=i)
			column.set_resizable(True)
			column.set_visible(False)
			self.subTreeview.append_column(column)
			
			renderer=gtk.CellRendererText()
			column=gtk.TreeViewColumn(streamListStore[i][0],renderer, text=i)
			column.set_resizable(True)
			column.set_visible(False)
			self.publishTreeview.append_column(column)
		
		col=self.getColumnByName('subscribed')
		self.subModel.set_visible_column(col)

		self.options.loadColumnViews()
		self.bar=self.builder.get_object('statusbar')
		self.context_id=self.bar.get_context_id('status bar')
		self.descriptionBox=self.builder.get_object('descriptionBox')
		self.descriptionBox.hide()
		self.builder.get_object('publishExpander').set_visible(False)
		
		self.indicator = gtk.Image()
		self.indicator.set_from_icon_name(gtk.STOCK_DISCONNECT,gtk.ICON_SIZE_MENU)
		self.indicator.show()
		self.bar.pack_end(self.indicator,False,False)
		#self.builder.get_object('indiBox').pack_start(self.indicator)
		
		self.ui = self.builder.get_object("ui")
		
		self.ui.show()
		
		
		if self.remote:
			self.getStreams()
		else:
			self.nGui=NetworkGui(_parent=self)
			if self.preferences.getCheckNetAtStart():
				self.nGui.show()
			checkVersion()
			
		
	def createMenu(self):
		menu_bar=self.builder.get_object("menu_bar")

		menu_item=gtk.MenuItem('Publish')
		menu_item.connect('activate',self.on_publishButton_clicked)
		menu_item.show()
		
		fileMenu=gtk.Menu()
		fileMenu.append(menu_item)
		
		
		if self.remote:
			menu_item=gtk.MenuItem('Quit Remote Daemon')
			menu_item.connect('activate',self.on_quitMenuItem_activate)
			menu_item.show()
		
			fileMenu.append(menu_item)
		else:
			menu_item=gtk.MenuItem('Remote Producer')
			menu_item.connect('activate',self.on_rProduceMenuItem_activate)
			menu_item.show()
		
			fileMenu.append(menu_item)
			
		menu_item=gtk.MenuItem('Exit')
		menu_item.connect('activate',self.on_exitMenuItem_activate)
		menu_item.show()
		
		fileMenu.append(menu_item)
			
		root_menu=gtk.MenuItem('File')
		root_menu.show()
		root_menu.set_submenu(fileMenu)
		menu_bar.append(root_menu)
		
		###create view menu
		collumnsItem=gtk.MenuItem('Visible columns')
		collumnsItem.show()
		
		viewMenu=gtk.Menu()
		viewMenu.append(collumnsItem)

		###create columns menu
		collumnsMenu=gtk.Menu()				
	
		for col in streamListStore:
			menu_item=gtk.CheckMenuItem(col[0])
			menu_item.set_name(col[0])
			menu_item.connect('toggled',self.on_col_toggled)
			menu_item.show()
			collumnsMenu.append(menu_item)
		
		collumnsItem.set_submenu(collumnsMenu)
		self.visibleCollumns=collumnsMenu

		root_menu=gtk.MenuItem('View')
		root_menu.show()
		root_menu.set_submenu(viewMenu)
		menu_bar.append(root_menu)
		
		###create log entry
		menu_item=gtk.MenuItem('Logger')
		menu_item.connect('activate',self.on_loggerMenuItem_activate)
		menu_item.show()
		viewMenu.append(menu_item)
		
		###create console entry
		menu_item=gtk.MenuItem('Console')
		menu_item.connect('activate',self.on_consoleMenuItem_activate)
		menu_item.show()
		viewMenu.append(menu_item)
		
		##create chat entry
		if not self.remote:
			menu_item=gtk.MenuItem('Chat')
			menu_item.connect('activate',self.on_chatMenuItem_activate)
			menu_item.show()
			viewMenu.append(menu_item)
		
		menu_item=gtk.MenuItem('Statitics')
		menu_item.connect('activate',self.on_statsMenuItem_activate)
		menu_item.show()
		viewMenu.append(menu_item)
		
		###create options menu
		
		menu_item=gtk.MenuItem('Preferences')
		menu_item.connect('activate',self.on_preferencesMenuItem_activate)
		menu_item.show()
		
		optionsMenu=gtk.Menu()
		optionsMenu.append(menu_item)
		
		
		menu_item=gtk.MenuItem('Measure Upload')
		menu_item.connect('activate',self.on_measureUploadMenuItem_activate)
		menu_item.show()
		
		#optionsMenu=gtk.Menu()
		optionsMenu.append(menu_item)
		
		root_menu=gtk.MenuItem('Options')
		root_menu.show()
		root_menu.set_submenu(optionsMenu)
		menu_bar.append(root_menu)
		
	
	def on_preferencesMenuItem_activate(self,widget):
		self.options.showUI()
		
	def on_measureUploadMenuItem_activate(self,widget=None):
		self.measureGui=MeasureUpload(self)
		
	def on_rProduceMenuItem_activate(self,widget):
		if not self.rProducerViewer:
			self.rProducerViewer=loadComponent('plugin','RemoteProducerUI')(_parent=self,parent=self)
		else:
			self.rProducerViewer.startUI()
		
	def on_loggerMenuItem_activate(self,widget):
		if self.logger:
			self.logger.start()
			
	def on_statsMenuItem_activate(self,widget):
		statsGui(self.interface,self.remote)
		
	def on_chatMenuItem_activate(self,widget):
		try:
			self.chatClientUI.show()
		except:
			self.chatClientUI=ChatClient(self)
			
			
	def on_consoleMenuItem_activate(self,widget):
		l = {'p2ner':self.root}
		start_console(l)

	def getStreams(self):
		self.interface.getStreams()
		reactor.callLater(1.0,self.getStreams)
		

	def updateSubStreams(self,streams):
		for stream in streams:
			self.builder.get_object('expander1').set_expanded(True)
			if not self.knownStreams.has_key(stream.id):
				self.knownStreams[stream.id]={}
				self.knownStreams[stream.id]['stream']=stream
				self.knownStreams[stream.id]['subscribed']=True
				self.knownStreams[stream.id]['valid']=True
			
				passwd=False
				if stream.password and stream.password!='None':
					passwd=True
		
				starttime='not valid'
				if stream.startTime!=0:
					starttime=strftime('%H:%M %A %d %m %y',localtime(stream.startTime))
				self.streamsModel.append((int(stream.id),stream.server[0],int(stream.server[1]),stream.title,stream.author,stream.type,bool(stream.live),starttime,bool(stream.startable),bool(stream.republish),passwd,True))
			else:
				self.knownStreams[stream.id]['subscribed']=True
				self.knownStreams[stream.id]['valid']=True
				
				live=self.getColumnByName('live')
				for s in self.streamsModel:
					if s[0]==stream.id:
						s[live]=bool(stream.live)
						break
				
	def updateRegStreams(self,streams):
		for stream in streams:			
			self.builder.get_object('publishExpander').set_visible(True)
			if not self.streams.has_key(stream.id):
				self.streams[stream.id]=stream
				passwd=False
				if stream.password:
					passwd=True
		
				starttime='not valid'
				if stream.startTime!=0:
					starttime=strftime('%H:%M %A %d %m %y',localtime(stream.startTime))
		
				self.publishModel.append((int(stream.id),stream.server[0],int(stream.server[1]),stream.title,stream.author,stream.type,bool(stream.live),starttime,bool(stream.startable),bool(stream.republish),passwd,True))
			else:
				live=self.getColumnByName('live')
				for s in self.publishModel:
					if s[0]==stream.id:
						s[live]=bool(stream.live)
						break
		
	def on_descriptionButton_toggled(self,widget):
		self.descriptionBox.set_visible(widget.get_active())
		
	def on_ui_destroy(self,widget,data=None):
		if self.logger:
			self.logger.stop()
		
		try:
			self.chatClientUI.on_ui_destroy()
		except:
			pass
		
		if not self.remote:
			self.interface.exiting()
		else:
			#self.interface.quit()
			reactor.stop()
	
	def on_exitMenuItem_activate(self,widget):
		self.ui.destroy()
	
	def on_quitMenuItem_activate(self,widget):
		if self.logger:
			self.logger.stop()
			
		
		self.interface.quiting()
		
		
	def on_col_toggled(self,widget):
		name=widget.get_label()
		for i in range(len(streamListStore)):
			if name==streamListStore[i][0]:
				break
		
		col=self.streamsTreeview.get_column(i)
		col.set_visible(widget.active)
		col=self.subTreeview.get_column(i)
		col.set_visible(widget.active)
		col=self.publishTreeview.get_column(i)
		col.set_visible(widget.active)
		
	def on_serversButton_clicked(self,widget):
		serversGUI(self,_parent=self)
	
	def on_refreshButton_clicked(self,widget=None):
		if not self.serversButtonClicked:
			self.servers=self.preferences.getActiveServers()
		self.contactServers()
		
		
	def setServers(self,servers):
		self.serversButtonClicked=True
		self.servers=servers
		self.contactServers()
		
	def contactServers(self):
		for s in self.knownStreams.values():
			s['valid']=False
		self.interface.contactServers(self.servers)


	def cleanStreams(self,s):
		check=[id for id in self.knownStreams.keys() if self.knownStreams[id]['stream'].server[0]==s[0] and self.knownStreams[id]['stream'].server[1]==int(s[1]) ] 
		
		for id in check:
			if self.knownStreams[id]['valid']==False:
				treeiter =self.streamsModel.get_iter_first()
				for s in self.streamsModel:
					if s[0]==id:
						self.streamsModel.remove(treeiter)
						break
					treeiter = self.streamsModel.iter_next(treeiter)

				self.knownStreams.pop(id)
		
				
	def getStream(self,streams,server):
		if streams==-1:
			self.cleanStreams(server)
			#message= 'server is unreachable: %s : %s '%(server[0],server[1])
			#self.newMessage(message,20)
			return
		
		for stream in streams:
			sub=False
			if stream.id in self.knownStreams.keys():
				sub=self.knownStreams[stream.id]['subscribed']
				treeiter =self.streamsModel.get_iter_first()
				for s in self.streamsModel:
					if s[0]==stream.id:
						self.streamsModel.remove(treeiter)
						break
					treeiter = self.streamsModel.iter_next(treeiter)

			self.knownStreams[stream.id]={}
			self.knownStreams[stream.id]['stream']=stream
			self.knownStreams[stream.id]['subscribed']=sub
			self.knownStreams[stream.id]['valid']=True
			
			#print stream
			passwd=False
			if stream.password and stream.password!='None':
				passwd=True
				
			starttime='not valid'
			if stream.startTime!=0:
				starttime=strftime('%H:%M %A %d %m %y',localtime(stream.startTime))

			self.streamsModel.append((int(stream.id),stream.server[0],int(stream.server[1]),stream.title,stream.author,stream.type,bool(stream.live),starttime,bool(stream.startable),bool(stream.republish),passwd,sub))
		self.cleanStreams(server)

	def on_streamsTreeview_row_activated(self,widget,path,col):
		child_model=self.get_child_model(self.streamsTreeview.get_model(),path=path)
		if child_model:
			path=child_model['path']
		col=self.getColumnByName('streamID')
		id=self.streamsModel[path][col]
		if self.knownStreams[id]['subscribed']:
			return
		ip=self.knownStreams[id]['stream'].server[0]
		port=self.knownStreams[id]['stream'].server[1]
		self.subscribeStream(id, ip, port)


	def on_subscribeButton_clicked(self,widget):
		treeselection=self.streamsTreeview.get_selection()
		(model, iter) = treeselection.get_selected()
		child_model=self.get_child_model(self.streamsTreeview.get_model(),iter=iter)
		if child_model:
			iter=child_model['iter']
		path = self.streamsModel.get_path(iter)
		col=self.getColumnByName('streamID')
		id=self.streamsModel[path][col]
		ip=self.knownStreams[id]['stream'].server[0]
		port=self.knownStreams[id]['stream'].server[1]
		self.subscribeStream(id, ip, port)
		
	
	def subscribeStream(self,id,ip,port,remote=False):
		if self.knownStreams[id].has_key('output') and not remote:
			output=self.knownStreams[id]['output']
		else:
			output=self.preferences.getAllComponents('output')
			if not output['default']:
				self.newMessage('select default output',20)
				return
			else:
				output=output['default']
			
		st=self.preferences.getSettings('output',output)
		
		out={}
		out['comp']=output
		out['kwargs']=st
		
		self.interface.subscribeStream(id,ip,port,out)
		
	def succesfulSubscription(self,stream,id):		
		if stream==-1:
			m='failed to subscribe stream with id:%d'%id
			self.newMessage(m,20)
			return
		id=stream.id
		self.knownStreams[id]['subscribed']=True
		self.builder.get_object('expander1').set_expanded(True)
		
		colid=self.getColumnByName('streamID')
		colsub=self.getColumnByName('subscribed')
		for s in self.streamsModel:
			if s[colid]==id:
				s[colsub]=True
				break
		
		self.builder.get_object("subscribeButton").set_sensitive(False)	
		

	def on_streamsTreeview_cursor_changed(self,widget):
		treeselection=self.streamsTreeview.get_selection()
		(model, iter) = treeselection.get_selected()
		col=self.getColumnByName('streamID')
		try:
			id=model.get_value(iter,col)
		except:
			return
		self.builder.get_object('descView').get_buffer().set_text(self.knownStreams[id]['stream'].getDesc())

		col=self.getColumnByName('subscribed')
		sub=model.get_value(iter,col)
		self.builder.get_object("subscribeButton").set_sensitive(not sub)
		
		self.builder.get_object("stopButton").set_sensitive(False)
		self.builder.get_object("startButton").set_sensitive(False)
		
	def on_subTreeview_cursor_changed(self,widget):
		treeselection=self.subTreeview.get_selection()
		(model, iter) = treeselection.get_selected()
		#path = self.subModel.get_path(iter)
		col=self.getColumnByName('startable')
		try:
			show=model.get_value(iter,col)
		except:
			return
		startButton = self.builder.get_object("startButton")
		startButton.set_sensitive(show)
		self.builder.get_object("stopButton").set_sensitive(True)
		col=self.getColumnByName('streamID')
		id=model.get_value(iter,col)
		self.builder.get_object('descView').get_buffer().set_text(self.knownStreams[id]['stream'].getDesc())
		
		self.lastSelectedId=id
		self.lastSelectedType='register'
		
		self.builder.get_object("subscribeButton").set_sensitive(False)
		self.builder.get_object("stopButton").set_sensitive(True)
		
		col=self.getColumnByName('live')
		live=model.get_value(iter,col)
		
		col=self.getColumnByName('startable')
		start=model.get_value(iter,col)
		
		if not live and start:
			self.builder.get_object("startButton").set_sensitive(True)
		else:
			self.builder.get_object("startButton").set_sensitive(False)
			
		
	def on_publishTreeview_cursor_changed(self,widget):
		treeselection=self.publishTreeview.get_selection()
		(model, iter) = treeselection.get_selected()
		col=self.getColumnByName('streamID')
		try:
			id=model.get_value(iter,col)
		except:
			return
		self.builder.get_object('descView').get_buffer().set_text(self.streams[id].getDesc())

		self.lastSelectedId=id
		self.lastSelectedType='produce'
		
		self.builder.get_object("subscribeButton").set_sensitive(False)
		self.builder.get_object("stopButton").set_sensitive(True)
		
		col=self.getColumnByName('live')
		live=model.get_value(iter,col)
		
		if not live:
			self.builder.get_object("startButton").set_sensitive(True)
		else:
			self.builder.get_object("startButton").set_sensitive(False)
			
			
	def on_activeButton_toggled(self,widget,search=True):
		if widget.get_active():
			model = self.streamsModel.filter_new(root=None)
			col=self.getColumnByName('live')
			model.set_visible_column(col)
			self.streamsTreeview.set_model(model)
		else:
			self.streamsTreeview.set_model(self.streamsModel)
		if search:
			self.on_searchButton_clicked(None)
		
	def get_child_model(self,model,iter=None,path=None):
		try:
			child_model=model.get_model()
		except:
			return False
			
		ret={}
		ret['model']=child_model
		if path:
			path = model.convert_path_to_child_path(path)
			ret['path']=path
		if iter:
			iter = model.convert_iter_to_child_iter(iter)
			ret['iter']=iter
		return ret	
	

	
	def on_stopButton_clicked(self,widget):
		if self.lastSelectedType=='produce':
			live=self.streams[self.lastSelectedId].live
			repub=False
			if not live:
				repub=True
				self.streams[self.lastSelectedId].republish=False
			self.interface.stopProducing(self.lastSelectedId,repub)
			
		elif self.lastSelectedType=='register':
			self.interface.unregisterStream(self.lastSelectedId)
		else:
			raise ValueError('problem on stop buttom clicked')

	

	def unregisterStream(self,id):
		self.knownStreams[id]['subscribed']=False
		col=self.getColumnByName('subscribed')
		colid=self.getColumnByName('streamID')
		for s in self.streamsModel:
			if s[colid]==id:
				s[col]=False
				break
			
		self.builder.get_object("stopButton").set_sensitive(False)
		self.builder.get_object("startButton").set_sensitive(False)
		
	def stopProducing(self,id):
		try:
			repub=self.streams[id].republish
		except:
			return
		col=self.getColumnByName('live')
		colid=self.getColumnByName('streamID')
		if not repub:
			self.streams.pop(id)
			treeiter =self.publishModel.get_iter_first()
			for s in self.publishModel:
				if s[colid]==id:
					self.publishModel.remove(treeiter)
					break
				treeiter = self.publishModel.iter_next(treeiter)
		else:
			self.streams[id].live=False
			for s in self.publishModel:
				if s[colid]==id:
					s[col]=False
					break
		self.builder.get_object("stopButton").set_sensitive(False)
		self.builder.get_object("startButton").set_sensitive(False)
			
		
		
		
	def on_startButton_clicked(self,widget):
		if self.lastSelectedType=='produce':
			self.interface.startProducing(self.lastSelectedId,self.lastSelectedType)
		elif self.lastSelectedType=='register':
			self.interface.startRemoteProducer(self.lastSelectedId,self.lastSelectedType)
		else:
			raise ValueError('problem on start buttom clicked')
		
		self.builder.get_object("startButton").set_sensitive(False)
	
	"""
	def changeStreamStatus(self,id,model):
		colid=self.getColumnByName('streamID')
		collive=self.getColumnByName('live')
		if model=='produce':
			self.streams[id].live=True
			m=self.publishModel
		else:
			self.knownStreams[id]['stream'].live=True
			m=self.streamsModel
			
		for s in m:
			if s[colid]==id:
				s[collive]=True
				break 
	"""	

	def on_searchButton_clicked(self,widget):
		searchEntry=self.builder.get_object('searchEntry')
		text = searchEntry.get_text()
		if not text:
			self.on_activeButton_toggled(self.builder.get_object('activeButton'),False)
			return
		modelFilter=self.streamsModel.filter_new()
		modelFilter.set_visible_func(self.showFilter,text)
		self.streamsTreeview.set_model(modelFilter)
		modelFilter.refilter()
		
	def showFilter(self,model,iter,text):
		#print model
		toggle=self.builder.get_object('activeButton').get_active()
		col=self.getColumnByName('live')
		active=self.streamsModel.get_value(iter,col)
		if not active and toggle:   
			return False
		
		for col in range(len(streamListStore)):
			if text in str(self.streamsModel.get_value(iter,col)):
				return True
		return False		

	def getColumnByName(self,text):
		col=[i for i in range(len(streamListStore)) if streamListStore[i][0]==text]
		return col[0]

	def on_publishButton_clicked(self,widget):
		ProducerGui(self,_parent=self)
	
	def registerStreamSettings(self,settings):
		input=settings.pop('input')
		output=self.preferences.getAllComponents('output')
		if not output['default']:
			self.newMessage('select default output',20)
			return
		st=self.preferences.getSettings('output',output['default'])
		out={}
		out['comp']=output['default']
		out['kwargs']=st
		self.interface.registerStream(settings,input,out)
		
	def registerStream(self,streams):
		if not streams:
			return
		
		if streams[0]==-1:
			m='failed to register stream'
			self.newMessage(m,20)
			return
		
		self.builder.get_object('publishExpander').set_visible(True)
		for stream in streams:
			#print 'loading stream'
			#print stream
			self.streams[stream.id]=stream
		
			passwd=False
			if stream.password:
				passwd=True
		
			starttime='not valid'
			if stream.startTime!=0:
				starttime=strftime('%H:%M %A %d %m %y',localtime(stream.startTime))
		
			self.publishModel.append((int(stream.id),stream.server[0],int(stream.server[1]),stream.title,stream.author,stream.type,bool(stream.live),starttime,bool(stream.startable),bool(stream.republish),passwd,True))


	def setLiveProducer(self,id,live):	
		self.streams[id].live=live
		colid=self.getColumnByName('streamID')
		col=self.getColumnByName('live')
		for s in self.publishModel:
			if id==s[colid]:
				s[col]=live
				
	def setLiveStream(self,id,live):
		colid=self.getColumnByName('streamID')
		if live:
			col=self.getColumnByName('live')
			self.knownStreams[id]['stream'].live=live
			for s in self.streamsModel:
				if id==s[colid]:
					s[col]=live
		else:
			self.knownStreams[id]['subscribed']=False
			col=self.getColumnByName('subscribed')
			for s in self.streamsModel:
				if id==s[colid]:
					s[col]=False	



	def on_streamsTreeview_button_press_event(self,treeview,event):
		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			time = event.time
			pthinfo = treeview.get_path_at_pos(x, y)
			if pthinfo is not None:
				path, col, cellx, celly = pthinfo
				treeview.grab_focus()
				treeview.set_cursor( path, col, 0)
				self.createOutputMenuPopUp(treeview,path).popup(None, None, None, event.button, time)
				return True
		return False


	def createOutputMenuPopUp(self,treeview,path):
		child = self.get_child_model(treeview.get_model(), path=path)
		if child:
			path=child['path']
		outputMenu=gtk.Menu()
		outMenu=gtk.MenuItem('Output')
		outMenu.show()
		outputMenu.append(outMenu)
		
		outputs=self.preferences.getAllComponents('output')
		compMenu=gtk.Menu()
		
		if outputs['comps']:
			out=outputs['comps'].pop()
			menu_item=gtk.RadioMenuItem(label=out)
			menu_item.connect("toggled", self.setOutputMethod,path)
			menu_item.show()
			if out==outputs['default']:
				menu_item.set_active(True)
			compMenu.append(menu_item)
			
		for out in outputs['comps']:
			menu_item=gtk.RadioMenuItem(group=menu_item,label=out)
			menu_item.connect("toggled", self.setOutputMethod,path)
			menu_item.show()
			if out==outputs['default']:
				menu_item.set_active(True)
			compMenu.append(menu_item)

			
		outMenu.set_submenu(compMenu)
		return outputMenu
	
		
	def setOutputMethod(self,widget,path):
		if not widget.get_active():
			return
		output=widget.get_label()
		col=self.getColumnByName('streamID')
		id=self.streamsModel[path][col]
		self.knownStreams[id]['output']=output

	def newMessage(self,message,severity):
		self.bar.pop(self.context_id)
		self.bar.push(self.context_id, message)
		
	def displayError(self,error,quit=False):
		error_dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR
					, message_format=error
					, buttons=gtk.BUTTONS_OK)
		error_dlg.run()
		error_dlg.destroy()
		if quit:
			self.ui.destroy()
			
		
		
	def networkStatus(self,status,ip,measure):
		#self.builder.connect_signals(self)
		#self.fileMenu.set_sensitive(True)
		if status:
			self.indicator.set_from_icon_name(gtk.STOCK_CONNECT,gtk.ICON_SIZE_MENU)
			#if self.preferences.getCheckAtStart():
			reactor.callLater(1,self.on_refreshButton_clicked,None)
			#self.builder.get_object('refreshButton').set_sensitive(True)
			#self.builder.get_object('serversButton').set_sensitive(True)
			
			self.extIP=ip
			if measure:
				self.on_measureUploadMenuItem_activate()
		else:
			if not self.remote:
				self.nGui.show()
			self.indicator.set_from_icon_name(gtk.STOCK_STOP,gtk.ICON_SIZE_MENU)
			
	def logNGui(self,text):
		self.nGui.addText(text)
		
	def getStreamsIds(self):
		colid=self.getColumnByName('streamID')
		colip=self.getColumnByName('ip')
		colport=self.getColumnByName('port')
		colsub=self.getColumnByName('subscribed')
		st=[(s[colid],s[colip],s[colport]) for s in self.streamsModel if s[colsub]]
		st +=[(s[colid],s[colip],s[colport]) for s in self.publishModel]
		return st
	
	def hasID(self,id):
		return self.knownStreams.has_key(id)
		
		
def startGui():
	clientGui()
	reactor.run()
				
if __name__=='__main__':
	startGui()
	

