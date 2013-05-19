from Resource import Resource

class NetworkResource(Resource):
	cacheable = True
	
	@property
	def is_wan(self):
		return self.broker.wan_name.lower() in self.name.lower()
	
	@property
	def is_public(self):
		return False
	
class DefaultNetworkResource(NetworkResource):
	__fields__ = (
		 ("address", str),
		 ("size", str),
		 ("public", bool),
		 ("netmask", str),
		 ("gateway", str),
		 ("vlan", str),
	)
	
	@property
	def is_public(self):
		return self.public

class VirtualWallNetworkResource(DefaultNetworkResource):
	__fields__ = (
		("type", str),
		("lossrate", float),
		("latency", int),
		("bandwidth", int),
		("protocol", str),
		("packetsize", int),
		("throughput", int),
	)
	
	@property
	def network_type(self):
		if self.protocol:
			return "active"
		return "managed"
