from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor,defer
from twisted.application.internet import MulticastServer 
import socket
import mupnp	

class upnpUI(object):
	
	def __init__(self, ip,gateway,proto):
		self.hp = mupnp.upnp(False,False,None);
		self.hp.UNIQ = True
		self.hp.VERBOSE = False
		self.hostIP=ip
		self.gateway=gateway
		self.proto=proto
		self.listenerMulticast=Listener(self.hp.ip,self.hp.port,'MULTICAST',self,gateway)
		
		
	
	#Actively search for UPNP devices
	def msearch(self,argc,argv):
		defaultST = "upnp:rootdevice"
		st = "schemas-upnp-org"
		myip = ''
		lport = self.hp.port
	
		if argc >= 3:
			if argc == 4:
				st = argv[1]
				searchType = argv[2]
				searchName = argv[3]
			else:
				searchType = argv[1]
				searchName = argv[2]
			st = "urn:%s:%s:%s:%s" % (st,searchType,searchName,self.hp.UPNP_VERSION.split('.')[0])
		else:
			st = defaultST
	
	
		#Build the request
		request = 	"M-SEARCH * HTTP/1.1\r\n"\
				"HOST:%s:%d\r\n"\
				"ST:%s\r\n" % (self.hp.ip,self.hp.port,st)
	
		for header,value in self.hp.msearchHeaders.iteritems():
				request += header + ':' + value + "\r\n"	
		request += "\r\n" 
		
	
		print "Entering discovery mode for '%s', Ctl+C to stop..." % st
		print ''
			
		
		self.listenerMulticast.send(request)
		
	

	def host(self,argc,argv):
		hp=self.hp
		indexList = []
		indexError = "Host index out of range. Try the 'host list' command to get a list of known hosts"
		if argc >= 2:
			action = argv[1]
			if action == 'list':
				ret={}
				if len(hp.ENUM_HOSTS) == 0:
					print "No known hosts - try running the 'msearch' or 'pcap' commands"
					return
				for index,hostInfo in hp.ENUM_HOSTS.iteritems():
					print "\t[%d] %s" % (index,hostInfo['name'])
					ip=hostInfo['name'].split(':')[0]
					ret[ip]=index
				return ret
			elif action == 'details':
				hostInfo = False
				if argc == 3:
					try:
						index = int(argv[2])
					except Exception, e:
						print indexError
						return
	
					if index < 0 or index >= len(hp.ENUM_HOSTS):
						print indexError
						return	
					hostInfo = hp.ENUM_HOSTS[index]
	
					try:
						#If this host data is already complete, just display it
						if hostInfo['dataComplete'] == True:
							hp.showCompleteHostInfo(index,False)
						else:
							print "Can't show host info because I don't have it. Please run 'host get %d'" % index
					except KeyboardInterrupt, e:
						pass
					return
	
			elif action == 'summary':
				if argc == 3:
				
					try:
						index = int(argv[2])
						hostInfo = hp.ENUM_HOSTS[index]
					except:
						print indexError
						return
	
					print 'Host:',hostInfo['name']
					print 'XML File:',hostInfo['xmlFile']
					for deviceName,deviceData in hostInfo['deviceList'].iteritems():
						print deviceName
						for k,v in deviceData.iteritems():
							try:
								v.has_key(False)
							except:
								print "\t%s: %s" % (k,v)
					print ''
					return
	
			elif action == 'info':
				output = hp.ENUM_HOSTS
				dataStructs = []
				for arg in argv[2:]:
					try:
						arg = int(arg)
					except:
						pass
					output = output[arg]
				try:
					for k,v in output.iteritems():
						try:
							v.has_key(False)
							dataStructs.append(k)
						except:
							print k,':',v
							continue
				except:
					print output
	
				ret=[]
				for struct in dataStructs:
					print struct,': {}'
					ret.append(struct)
				return ret
			elif action == 'get':
				hostInfo = False
				if argc == 3:
					try:
						index = int(argv[2])
					except:
						print indexError
						return
					if index < 0 or index >= len(hp.ENUM_HOSTS):
							print "Host index out of range. Try the 'host list' command to get a list of known hosts"
							return	
					else:
						hostInfo = hp.ENUM_HOSTS[index]
	
						#If this host data is already complete, just display it
						if hostInfo['dataComplete'] == True:
							print 'Data for this host has already been enumerated!'
							return
	
						try:
							#Get extended device and service information
							if hostInfo != False:
								print "Requesting device and service info for %s (this could take a few seconds)..." % hostInfo['name']
								print ''
								if hostInfo['dataComplete'] == False:
									(xmlHeaders,xmlData) = hp.getXML(hostInfo['xmlFile'])
									if xmlData == False:
										print 'Failed to request host XML file:',hostInfo['xmlFile']
										return
									if hp.getHostInfo(xmlData,xmlHeaders,index) == False:
										print "Failed to get device/service info for %s..." % hostInfo['name']
										return
								print 'Host data enumeration complete!'
								
								return
						except KeyboardInterrupt, e:
							return
	
			elif action == 'send':
				#Send SOAP requests
				index = False
				inArgCounter = 0
				
				numReqArgs = 6
				extraArgs = argc-numReqArgs
				
				
				try:
					index = int(argv[2])
				except:
					print indexError
					return
				deviceName = argv[3]
				serviceName = argv[4]
				actionName = argv[5]
				hostInfo = hp.ENUM_HOSTS[index]
				actionArgs = False
				sendArgs = {}
				retTags = []
				controlURL = False
				fullServiceName = False

				#Get the service control URL and full service name
				try:
					controlURL = hostInfo['proto'] + hostInfo['name']
					controlURL2 = hostInfo['deviceList'][deviceName]['services'][serviceName]['controlURL']
					if not controlURL.endswith('/') and not controlURL2.startswith('/'):
						controlURL += '/'
					controlURL += controlURL2
				except Exception,e:
					print 'Caught exception:',e
					print "Are you sure you've run 'host get %d' and specified the correct service name?" % index
					return 2

				#Get action info
				try:
					actionArgs = hostInfo['deviceList'][deviceName]['services'][serviceName]['actions'][actionName]['arguments']
					fullServiceName = hostInfo['deviceList'][deviceName]['services'][serviceName]['fullName']
				except Exception,e:
					print 'Caught exception:',e
					print "Are you sure you've specified the correct action?"
					return 2

				extraArgsUsed = 0
				for argName,argVals in actionArgs.iteritems():
					actionStateVar = argVals['relatedStateVariable']
					stateVar = hostInfo['deviceList'][deviceName]['services'][serviceName]['serviceStateVariables'][actionStateVar]

					if argVals['direction'].lower() == 'in':
						if extraArgs-extraArgsUsed > 0:
							arg = argv[numReqArgs+extraArgsUsed]
							print "Using ", arg, " for ", argName
							sendArgs[argName] = (arg,stateVar['dataType'])
							extraArgsUsed += 1
						
					else:
						retTags.append((argName,stateVar['dataType']))


				#print 'Requesting',controlURL
				soapResponse = hp.sendSOAP(hostInfo['name'],fullServiceName,controlURL,actionName,sendArgs)
				if soapResponse != False:
					#It's easier to just parse this ourselves...
					ret={0:0}
					for (tag,dataType) in retTags:
						tagValue = hp.extractSingleTag(soapResponse,tag)
						if dataType == 'bin.base64' and tagValue != None:
							tagValue = base64.decodestring(tagValue)
						print tag,':',tagValue
						ret[tag]=tagValue
					return ret
				else:
					return False
				return
	
	
		return
	

	def discover(self):
		self.d=defer.Deferred()
		self.listenerMulticast.startListeningMulticast()
		reactor.callLater(0.1,self.msearch,0,[])
		return self.d
	
	def gotResponse(self,data):
		f=self.hp.parseSSDPInfo(data,False,False)
		if f:
			self.listenerMulticast.stopListening()
			ret=self.host(2,['host','list'])
			self.hostnum=ret[self.gateway[0]]
			self.host(3,['host','get','0'])
			try:
				ret=self.host(6 ,['host', 'info', '0', 'deviceList','WANConnectionDevice', 'services'])
			except:
				self.d.errback('upnp device not compatible')
				return
			self.type='WANPPPConnection'
			if self.type not in ret:
				self.type='WANIPConnection'
			self.d.callback(True)
		else:
			#self.d.errback("couldn't parse response")
			pass
			#print 'problemmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm'
			"""
			self.host(3,['host','get','0'])
                        self.host(8,['host', 'info' ,'0', 'deviceList' ,'WANConnectionDevice'])
#			self.host(8,['host', 'info' ,'0', 'deviceList' ,'WANConnectionDevice' ,'services' ,'WANPPPConnection' ,'actions' ])
#			self.host(6, ['host', 'send', '0', 'WANConnectionDevice', 'WANPPPConnection', 'GetUserName'])
			self.host(14,['host', 'send', '0', 'WANConnectionDevice', 'WANPPPConnection', 'AddPortMapping', 'P2NER UDP for control messages', '0', self.hostIP, '1', self.control_port,'', 'UDP', self.control_port])
                        self.host(14,['host', 'send', '0', 'WANConnectionDevice', 'WANPPPConnection', 'AddPortMapping', 'P2NER UDP for data transfer', '0', self.hostIP, '1', self.data_port,'', 'UDP', self.data_port])
#			self.host(9 ,['host', 'send', '0', 'WANConnectionDevice', 'WANPPPConnection', 'GetSpecificPortMappingEntry', '9100', '', 'UDP'])
#			self.host(9 ,['host', 'send', '0', 'WANConnectionDevice', 'WANPPPConnection', 'DeletePortMapping', 'UDP', '9100', ''])
#			self.host(9 ,['host', 'send', '0', 'WANConnectionDevice', 'WANPPPConnection', 'GetSpecificPortMappingEntry', '9100', '', 'UDP'])
#			self.d.callback('ok')
			"""
	
	def upnpFailed(self):
		self.d.errback("no upnp device found after 15 seconds")
		
	def getSpecificPortMapping(self,port,exPort):
		#self.host(3,['host','get','0'])
		ret=self.host(9 ,['host', 'send', self.hostnum, 'WANConnectionDevice', self.type, 'GetSpecificPortMappingEntry', exPort, '', self.proto])
		

		if ret==2:
			return (2,)
		elif ret:
			if str(self.hostIP)!=str(ret['NewInternalClient']):
				print 'port is forwarded for another peer'
				return (3,str(ret['NewInternalClient']))
			if int(ret['NewInternalPort'])!=port:
				print 'port is mapped to another port'
				return (4,int(ret['NewInternalPort']))
			else:
				return (0,)
		else:
			return (1,)

		
	def addPortMapping(self,port,exPort):
		#self.host(8,['host', 'info' ,'0', 'deviceList' ,'WANConnectionDevice'])
		ret=self.host(14,['host', 'send', self.hostnum, 'WANConnectionDevice', self.type, 'AddPortMapping', str(exPort), '0', self.hostIP, '1',exPort,'', self.proto, port])
		
		if ret and ret!=2:
			return (True,exPort)
		else:
			return (False,exPort)
		
class Listener(DatagramProtocol):
	
	def __init__(self,ip,port,interface,controler,gateway):
		self.ip=ip
		self.port=port
		self.controler=controler
		self.interface=interface
		self.upnpFound=False
		self.failed=False
		self.gateway=gateway
		
		
	def datagramReceived(self, data, (host, port)):
		#print "received to interface %s from %s:%d\n %r" % (self.interface, host, port, data)
		if host in self.gateway:
			#print "received to interface %s from %s:%d\n %r" % (self.interface, host, port, data)

			#print "gateway found ",host
			self.upnpFound=True
			self.controler.gotResponse(data)
			
	
	def send(self,data):
		reactor.callLater(15,self.check)
		self.sendData(data)
		
	def sendData(self,data):
		if not self.failed and not self.upnpFound:
			#print "sending data"
			#print data
			self.transport.write(data, (self.ip, self.port))
			reactor.callLater(0.5,self.sendData,data)
			
	def check(self):
		if not self.upnpFound:
			self.controler.upnpFailed()
			self.failed=True
		
		
	def startListeningMulticast(self):
		self.sock=reactor.listenMulticast(1910,self)
		self.sock.joinGroup(self.ip,socket.INADDR_ANY)
		
	def stopListening(self):
		self.sock.stopListening()
		pass




