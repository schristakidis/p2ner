'''
Created on 21.02.2011

@author: kca
'''

from bonfire import Entity
from copy import copy

class UserAPIEntity(Entity):
	__list_fields= {}
	
	def __init__(self, userapi = None, fields = False, *args, **kw):
		super(UserAPIEntity, self).__init__(fields = fields, *args, **kw)
		self.__userapi = userapi
		self._init()
		
	def _init(self):
		self._old = {}
		for f in self.get_fields():
			self._old[f[0]] = copy(getattr(self, f[0]))
		
	def _get_userapi(self):
		return self.__userapi
	def _set_userapi(self, userapi):
		self.__userapi = userapi
	_userapi = property(_get_userapi, _set_userapi)
	
	def get_is_persistent(self):
		return self._userapi is not None
	is_persistent = property(get_is_persistent)
	
	def __eq__(self, o):
		return o is self or (o.__class__ == self.__class__ and o.id == self.id)
	
	def __hash__(self):
		return hash(self.id)
	
	@classmethod
	def get_listfields(cls):
		try:
			return cls.__list_fields[cls]
		except KeyError:
			cls.__list_fields[cls] = [ f for f in cls.get_fields() if isinstance(f[1], (list, set, tuple, frozenset)) ]
			return cls.__list_fields[cls]
		