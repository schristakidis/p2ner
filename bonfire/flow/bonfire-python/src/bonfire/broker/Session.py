'''
Created on 08.11.2011

@author: kca
'''

from collections import defaultdict

class Session(object):
	def __init__(self, broker, user, *args, **kw):
		super(Session, self).__init__(*args, **kw)
		self.__entities = defaultdict(dict)
		self.user = user
		
	