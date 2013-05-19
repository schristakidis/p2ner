'''
Created on 24.11.2010

@author: kca
'''

from bonfire import Entity 

class DynamicReference(object):
	def __init__(self, href = None, name = None, groups = None, *args, **kw):
		super(DynamicReference, self).__init__(*args, **kw)
		self.groups = groups
		self.__href = href
		if not href:
			assert name
			self.__name = name
			
	def get(self):
		return self.__href and ("href", self.__href) or ("name", self.__name)

class BasicBrokerEntity(Entity):
	def __init__(self, broker = None, xml = None, fields = False, user = None, *args, **kw): 
		super(BasicBrokerEntity, self).__init__(fields = fields, *args, **kw)
		
		self.__broker = broker
		self.__xml = xml
		self.__user = user
	
	def get_broker(self):
		return self.__broker
	broker = property(get_broker)
	
	def _set_broker(self, broker):
		self.__broker = broker
	_broker = property(get_broker, _set_broker)
	
	def get_xml(self):
		#from occi import toprettyxml
		#if self.__xml is None:
		#	self.__xml = toprettyxml(self)
		return self.__xml
	xml = property(get_xml)
	
	def _set_xml(self, xml):
		self.__xml = xml
	_xml = property(get_xml, _set_xml)
	
	def _set_user(self, user):
		self.__user = user
		
	@property
	def _user(self):
		return self.__user
	
	@property
	def logger(self):
		from bonfire.broker import logger
		return logger

class BrokerEntity(BasicBrokerEntity):
	cacheable = False

	__fields__ = (
			("groups", str),
	)
	
	def __init__(self, name, url = None, broker = None, xml = None, fields = False, user = None, *args, **kw):
		super(BrokerEntity, self).__init__(broker = broker, xml = xml, fields = fields, user = user, *args, **kw)
		
		self.__name = name
		self.__url = url
		
	def __getattr__(self, name):
		#TODO be smarter here	
		self.prefetch()
		return super(BrokerEntity, self).__getattr__(name)
	
	def needs_prefetching(self):
		return self._get_fields() is None
	
	def prefetch(self):
		if self._get_fields() is None:
			self.refresh()
			
	def refresh(self):
		self._set_fields(self.broker._get_fields(self, self._user))
			
	def get_url(self):
		return self.__url
	url = property(get_url)
	id = url
	
	def __str__(self):
		return self.id
	
	@property
	def short_id(self):
		return self.url.rpartition("/")[-1]
	
	def get_name(self):
		return self.__name
	name = property(get_name)
	
	def name_matches(self, pattern):
		if not hasattr(pattern, "match"):
			import re
			pattern = re.compile(self.broker.aggregator_image_name, re.I)
			
		return pattern.match(self.name)
	
	@property
	def group(self):
		return self.groups
	
	def __setattr__(self, k, v):
		if k == "name":
			self.__name = v
		else:
			super(BrokerEntity, self).__setattr__(k, v)
		