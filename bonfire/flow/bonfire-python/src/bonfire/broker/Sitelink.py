from Resource import Resource
from BrokerEntity import BasicBrokerEntity
from Site import Site

class AutobahnEndpoint(BasicBrokerEntity):
	__fields__ = (
			("location", Site),
			("vlan", str),
	)
	
	def __init__(self, location = None, *args, **kw):
		super(Endpoint, self).__init__(*args, **kw)
		
		if location is not None:
			self.location = location
		
	@property
	def target_location(self):
		return self.location
	
	@property
	def href(self):
		return self.location

Endpoint = AutobahnEndpoint

class Sitelink(Resource):
	__fields__ = (
			("endpoint", [ AutobahnEndpoint ]),
			("bandwidth", str),
			("state", str),
	)
	
	@property
	def end_point(self):
		return self.endpoint	 
	
	@property
	def is_active(self):
		return self.status and self.status.lower() in ("ready", "active", "up", "on", "running")
	
	
	@property
	def status(self):
		return self.state