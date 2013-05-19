'''
Created on 24.11.2010

@author: kca
'''

from BrokerEntity import BrokerEntity

class Resource(BrokerEntity):
	__fields__ = (
		("description", unicode),
	)
	
	def __init__(self, name, location, experiment = None, *args, **kw):
		super(Resource, self).__init__(name = name, *args, **kw)
		
		self.__experiment = experiment
		self.__location = location
		
	def _set_fields(self, fields):
		super(Resource, self)._set_fields(fields)
		if not self.__experiment:
			self.__experiment = fields.experiment
		
	def get_location(self): 
		return self.__location
	location = property(get_location)
	
	def get_experiment(self):
		return self.__experiment 
	def set_experiment(self, e):
		self.__experiment = e
	experiment = property(get_experiment, set_experiment)
	
	@property
	def groups(self):
		return self.gname and self.gname.split(",") or ()
	
	def add_group(self, group):
		groups = list(self.groups)
		if group not in groups:
			groups.append(group)
			self.gname = ','.join(groups)
			
	def remove_group(self, group):
		groups = list(self.groups)
		try:
			groups.remove(group)
			self.gname = ','.join(groups)
		except ValueError:
			pass
	
