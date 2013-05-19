'''
Created on 19.03.2013

@author: kca
'''

from bonfire.exc import BonfireError

class CommunicationError(BonfireError):
	pass

class TransportError(CommunicationError):
	pass

class RemoteError(CommunicationError):
	def __init__(self, msg, code = 0, *args, **kw):
		super(RemoteError, self).__init__(msg, *args, **kw)
		self.code = code
