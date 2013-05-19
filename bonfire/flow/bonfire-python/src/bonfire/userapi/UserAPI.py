'''
Created on 10.02.2011

@author: kca
'''

from abc import ABCMeta, abstractmethod
import string
from bonfire.userapi.exc import IllegalUID

class UserAPI(object):
	__metaclass__ = ABCMeta
	
	LEGAL_CHARS = string.lowercase + string.digits + "-_"

	@classmethod
	def assert_legal_uid(klass, uid):
		if not isinstance(uid, basestring):
			raise IllegalUID("Expected a string, not %s" % (uid, ))
		if not uid:
			raise IllegalUID("Empty string not allowed.")

		for c in uid[:-1]:
			if c not in klass.LEGAL_CHARS:
				if c in string.uppercase:
					raise IllegalUID("Only lowercase characters allowed")
				raise IllegalUID("Illegal character '%s'" % (c,))
			
		if uid[-1] not in klass.LEGAL_CHARS + "$":
			raise IllegalUID("Illegal character '%s'" % (uid[-1],))
	
	@classmethod
	def is_legal_uid(klass, uid):
		try:
			klass.assert_legal_uid(uid)
			return True
		except IllegalUID:
			return False
	
	@abstractmethod
	def list_users(self):
		raise NotImplementedError()
	
	@abstractmethod
	def get_user(self, uid):
		raise NotImplementedError()
	
	@abstractmethod
	def persist(self, entity):
		raise NotImplementedError()
	
	def get_logger(self):
		from bonfire.userapi import logger
		return logger
	logger = property(get_logger)
