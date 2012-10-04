import sys,subprocess
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


def getGateway():
	gateway=[]
	if 'linux' in sys.platform:
		try:
			route=subprocess.check_output(['/sbin/route','-n'])
		except:
			route = subprocess.Popen(['/sbin/route','-n'], stdout=subprocess.PIPE).communicate()[0]

		route=[r.split() for r in route.splitlines()]
		route=route[2:]
		gateway=[g[1] for g in route if 'G' in g[3]]
	elif 'win' in sys.platform:
		import wmi
		c = wmi.WMI ()
		
		for interface in c.Win32_NetworkAdapterConfiguration (IPEnabled=1):
			#print interface.Description, interface.MACAddress
			for ip_address in interface.DefaultIPGateway:
				gateway.append(ip_address)
	else:
		print "operating system not supported"
		return False
		
	if gateway:
		return gateway
	else:
		return False
			


def getIP():
	ip=[]
	if 'linux' in sys.platform:
		"""
		ifconf=subprocess.check_output('/sbin/ifconfig')
		f=ifconf.split('inet addr:')
		for line in f[1:]:
			line=line.split()
			if line[0]!='127.0.0.1':
				ip.append(line[0])
		"""
		from socket import socket, SOCK_DGRAM, AF_INET
		s = socket(AF_INET, SOCK_DGRAM)	
		s.connect(('google.com', 0))
		ip=s.getsockname()
		s.close()
		if ip:
			ip=[ip[0]] 
	elif 'win' in sys.platform:
		import wmi
		c = wmi.WMI ()

		for interface in c.Win32_NetworkAdapterConfiguration (IPEnabled=1):	
			for ip_address in interface.IPAddress:
				if '.' in ip_address and ip_address!='127.0.0.1':
					ip.append(ip_address)	
	else:
		print "operating system not supported"
		return False	
		
	if ip:
		return ip
	else:
		return False
	
def isLocalIP(ip):
	if ip.startswith('192.168.'):
		return True
	else:
		return False
	

if __name__=='__main__':
	print getGateway()
	print getIP()
	
