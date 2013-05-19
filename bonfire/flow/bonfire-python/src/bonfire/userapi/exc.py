#! /usr/bin/env python

'''
Created on 14.02.2011

@author: kca
'''

from bonfire.exc import BonfireError
from bonfire.http.exc import CommunicationError

class UserApiError(BonfireError):
	pass 

class NotFound(UserApiError):
	pass
UnknownUserError = NotFound

class WeAreFull(UserApiError):
	pass

class CommunicationError(UserApiError, CommunicationError):
	pass

class IllegalUID(UserApiError, ValueError):
	pass

class OperationalError(UserApiError):
	pass