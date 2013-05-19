'''
Created on 10.02.2011

@author: kca
'''

from bonfire.exc import BonfireError

class BrokerError(BonfireError):
	pass

class UnknownEntityType(BrokerError):
	pass

class TotallySurprisedError(BrokerError):
	pass
		
class OCCIError(BrokerError):
	pass

class IllegalFieldType(BrokerError, TypeError):
	pass

class NotFound(BrokerError):
	pass