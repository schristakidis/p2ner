from Resource import Resource
from BrokerEntity import BasicBrokerEntity

class Interface(BasicBrokerEntity):
	def __init__(self, name = None, physical_interface = None, ip = None, netmask = None, *args, **kw):
		super(Interface, self).__init__(*args, **kw)
		if name is not None:
			self.name = name
		if ip is not None:
			self.ip = ip
		if netmask is not None:
			self.netmask = netmask
		if physical_interface is not None:
			self.physical_interface = physical_interface
	
	__fields__ = (
		("name", str),
		("physical_interface", str),
		("ip", str),
		("netmask", str)
	)

class Router(Resource):
	__fields__ = (
		("host", str),
		("interface", [ Interface ]),
		("config", str),
		("state", str)
	)
	
	@property
	def is_active(self):
		return self.status and self.status.lower() in ("ready", "active", "up", "on", "running")
	
	@property
	def is_pending(self):
		return self.status and self.status.lower() in ("pending")

	
class PhysicalInterfaceTarget(BasicBrokerEntity):
	__fields__ = (
		("host", str),
		("physical_interface", str)
	)
	
class PhysicalInterface(BasicBrokerEntity):
	__fields__ = (
		("name", str),
		("connected_to", PhysicalInterfaceTarget)
	)
	
class PhysicalRouter(BasicBrokerEntity):
	__fields__ = (
		("name", str),
		("description", str),
		("interface", [ PhysicalInterface ])	
	)
	
	@property
	def id(self):
		return self.name
	
	@property
	def status(self):
		return self.state
	
class PhysicalNode(BasicBrokerEntity):
	__fields__ = (
		("name", str),
		("description", str),
		("interface", [ PhysicalInterface ])	
	)
	
class FedericaEndpoint(BasicBrokerEntity):
	__fields__ = (
		("router", Router),
		("router_interface", str)
	)
	
	def __init__(self, router = None, router_interface = None, *args, **kw):
		super(FedericaEndpoint, self).__init__(*args, **kw)
		
		if router is not None:
			self.router = router
		if router_interface is not None:
			self.router_interface = router_interface 
	
class NetworkLink(BasicBrokerEntity):
	__fields__ = (
		("endpoint", [ FedericaEndpoint ]),
	)
	
class FedericaNetwork(Resource):
	__fields__ = (
		("state", str),
		("network_link", [ NetworkLink ]),
		("vlan", str)
	)
	
	@property
	def is_active(self):
		return self.status and self.status.lower() in ("ready", "active", "up", "on", "running")
	
	
	@property
	def status(self):
		return self.state