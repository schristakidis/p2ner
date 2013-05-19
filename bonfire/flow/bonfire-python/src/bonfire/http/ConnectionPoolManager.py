'''
Created on 19.03.2013

@author: kca
'''

from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

from bonfire.http import logger

class Urllib3ResponseWrapper(object):
	def __init__(self, response, *args, **kw):
		super(Urllib3ResponseWrapper, self).__init__(*args, **kw)
		
		self.__response = response
		
	def __getattr__(self, k):
		return getattr(self.__response, k)
	
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()
		
	def close(self):
		self.__response.release_conn()
		
	def isclosed(self):
		return False

class PoolConnectionWrapper(object):
	def __init__(self, connection, pool, *args, **kw):
		self.__connection = connection
		self.__pool = pool
		
	def __getattr__(self, k):
		return getattr(self.__connection, k)

class ConnectionPoolManager(object):
	def __init__(self, host, port, certfile = None, keyfile = None, force_ssl = False, *args, **kw):
		super(ConnectionPoolManager, self).__init__(*args, **kw)
		
		logger.debug("Creating ConnectionPoolManager for %s:%s", host, port)

		if certfile or keyfile or force_ssl:
			self.__pool = HTTPSConnectionPool(host, port, maxsize = 16, cert_file = certfile, key_file = keyfile)
		else:
			self.__pool = HTTPConnectionPool(host, port, maxsize = 16)
			
	def request(self, method, path, body, headers, timeout):
		return Urllib3ResponseWrapper(self.__pool.urlopen(method, path, body, 
			headers, timeout = timeout, pool_timeout = 30, preload_content = False))
			
		
		