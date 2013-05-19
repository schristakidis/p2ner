'''
Created on 15.05.2012

@author: kca
'''
from bonfire.Entity import Entity

class Reservation(Entity):
	__fields__ = (
		("uid", str),
		("state", str),
	)
	
	def __init__(self, url, name, broker, user, fields, *args, **kw):
		super(Reservation, self).__init__(fields = fields, *args, **kw)
		self.__url = url
		self.__name = name
		self._broker = broker
		self._user = user
		self.__details = None
		
	@property
	def id(self):
		return self.uid
	
	@property
	def url(self):
		return self.__url
		
	@property
	def name(self):
		return self.__name
	
	@property
	def running(self):
		return self.state.lower() == "running"
	
	def __getattr__(self, name):
		try:
			return super(Reservation, self).__getattr__(name)
		except AttributeError, e:
			self.prefetch()
			try:
				return self.__details[name]
			except KeyError:
				raise e
		
	def prefetch(self):
		if self.__details is None:
			self.refresh()
			
	def refresh(self):
		self.__details = self._broker._get_reservation_details(self, self._user)
		
	def needs_prefetching(self):
		return self.__details is None
	