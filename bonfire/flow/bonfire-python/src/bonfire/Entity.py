'''
Created on 21.02.2011

@author: kca
'''

from abc import ABCMeta
from collections import namedtuple
from copy import copy

class EntityType(ABCMeta):
	@property
	def __displayname__(self):
		return self.__name__
	
class Attribute(namedtuple("AttributeBase", ("name", "type", "default"))):
	def __new__(cls, name, type, default = None):
		if default is None and isinstance(type, (tuple, list, set, frozenset)):
			default = []
		return super(Attribute, cls).__new__(cls, name = name, type = type, default = default)
	
	def __iter__(self):
		yield self.name
		yield self.type

class Entity(object):
	__metaclass__ = EntityType
	
	__fields__ = ()
	
	__ignore__ = ()
	
	__fields = None
	
	__field_cache = {}

	def __init__(self, fields = False, *args, **kw):
		super(Entity, self).__init__(*args, **kw)
		
		if fields is not False:
			assert(fields is None or isinstance(fields, dict))
			self.__fields = fields
		else:
			#print("initializing fields for %s" % (self, ))
			self.__fields = {}
			for field in self.get_fields():
				if not isinstance(field, Attribute):
					field = Attribute(*field)
				self.__fields[field.name] = copy(field.default)

		
	def __getattr__(self, name):
		#the following 2 lines are pretty useless, but catch a really nasty error that occurs when I fuck up again in a certain place
		if name == "_Entity__broker":
			raise NotImplementedError()
		
		try:
			return self.__fields[name]
		except (KeyError, TypeError):
			raise AttributeError("%s object has no attribute %s" % (self.__class__.__name__, name))
	
	def __setattr__(self, k, v):
		#TODO: hack.
		if k.startswith("_") or k == "experiment":
			return super(Entity, self).__setattr__(k, v)
		if self.__fields is None:
			raise NotImplementedError()
		if k not in self.__fields:
			raise AttributeError(k)
		self.__fields[k] = v 
	
	@classmethod
	def get_fields(klass):
		try:
			return Entity.__field_cache[klass]
		except KeyError:
			fields = []
			
			bases = list(klass.__mro__)
			bases.reverse()
			for c in bases:
				fields += list(c.__dict__.get("__fields__", []))

			Entity.__field_cache[klass] = fields
			return fields

	@classmethod
	def get_field_type(klass, name):
		for f in klass.get_fields():
			if f[0] == name:
				return f[1]
		raise KeyError("No such attribute on %s: %s" % (klass.__name__, name))
	
	def _get_fields(self):
		return self.__fields
	def _set_fields(self, fields):
		self.__fields = fields.values
	
	def __hash__(self):
		return hash(self.id)
	
	def __eq__(self, o):
		return self is o or (hasattr(o, "id") and o.id == self.id)
	
	def __ne__(self, o):
		return not (self == o)
