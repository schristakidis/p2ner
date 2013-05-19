'''
Created on 21.05.2011

@author: kca
'''

from urlparse import urlparse
from base64 import b64encode
from bonfire.http import logger
from exc import CommunicationError, RemoteError
from cStringIO import StringIO
from datetime import datetime
from urllib2 import quote
from time import time
from logging import DEBUG
from socket import getservbyname

def compose_qs(values):
	return "&".join([ "%s=%s" % (quote(k), quote(v)) for k, v in dict(values).iteritems() ])

class LoggingResponseWrapper(object):
	logger = logger
	
	def __init__(self, response, *args, **kw):
		super(LoggingResponseWrapper, self).__init__(*args, **kw)
		self.__response = response
		self.__buffer = StringIO()
		self.__finalized = False
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()
		
	def __enter__(self):
		return self
	
	def read(self, n = None):
		s = self.__response.read(n)
		self.__buffer.write(s)
		return s
	
	def readline(self):
		s = self.__response.readline()
		self.__buffer.write(s)
		return s
	
	def readlines(self, sizehint = None):
		lines = self.__response.readlines(sizehint)
		self.__buffer.write(''.join(lines))
		return lines
	
	def close(self):
		if self.__finalized:
			logger.debug("%s is already finalized" % (self, ))
			return 
		
		self.__finalized = True
		try:
			if not self.__response.isclosed():
				self.__buffer.write(self.__response.read())
			logger.debug("Read data:\n %s", self.__buffer.getvalue())
		except:
			logger.exception("Finalizing response failed")
		finally:
			self.__response.close()
				
		self.__buffer.close()
		
class CachingHttplibResponseWrapper(object):
	def __init__(self, response, path, tag, last_modified, cache, *args, **kw):
		super(CachingHttplibResponseWrapper, self).__init__(*args, **kw)
		self.__cache = cache
		self.__buffer = StringIO()
		self.__path = path
		self.__tag = tag
		self.__response = response
		self.__last_modified = last_modified
		self.__finalized = False
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()
		
	def __enter__(self):
		return self
	
	def read(self, n = None):
		s = self.__response.read(n)
		self.__buffer.write(s)
		return s
	
	def readline(self):
		s = self.__response.readline()
		self.__buffer.write(s)
		return s
	
	def readlines(self, sizehint = None):
		lines = self.__response.readlines(sizehint)
		self.__buffer.write(''.join(lines))
		return lines
	
	def close(self):
		if self.__finalized:
			logger.debug("%s is already finalized" % (self, ))
			return 
		
		self.__finalized = True
		try:
			if not self.__response.isclosed():
				self.__buffer.write(self.__response.read())
			val = self.__buffer.getvalue()
			logger.debug("Putting to cache: %s -> %s, %s\n %s", self.__path, self.__tag, self.__last_modified, val)
			self.__cache[self.__path] = (self.__tag, self.__last_modified, val)
		except:
			logger.exception("Finalizing response failed")
		finally:
			self.__response.close()
				
		self.__buffer.close()
		
class closing(object):
	def __init__(self, o, *args, **kw):
		super(closing, self).__init__(*args, **kw)
		self.__o = o

	def __getattr__(self, k):
		return getattr(self.__o, k)

	def __enter__(self):
		return self.__o

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__o.close()

	def close(self):
		self.__o.close()
	
class RestClient(object):
	logger = logger
	ERROR_RESPONSE_MAX = 320
	
	get_timeout = timeout = 120.0
	
	def __init__(self, uri, username = None, password = None, certfile = None, 
				keyfile = None, content_type = "text/plain", headers = None, 
				cache = True, timeout = None, get_timeout = None, 
				component_name = "broker", connection_manager = None,
				*args, **kw):			 
		super(RestClient, self).__init__(*args, **kw)
		
		self.logger.info("Creating RestClient for %s", uri)
		
		self.timeout = timeout or self.timeout
		self.get_timeout = get_timeout or timeout or self.get_timeout

		if cache:
			if cache is True:
				from bonfire.util import LRUCache
				cache = LRUCache()
			self.__cache = cache
					
		if "://" not in uri:
			uri = "http://" + uri
		
		self.__content_type = content_type
		self.component_name = component_name
		
		info = urlparse(uri)
		
		if info.scheme == "https":
			if bool(certfile) ^ bool(keyfile):
				raise ValueError("Must give both certfile and keyfile if any")
			if certfile:
				from os.path import exists
				if not exists(certfile):
					raise ValueError("Certificate file not found: %s" % (certfile, ))
				if not exists(keyfile):
					raise ValueError("Key file not found: %s" % (keyfile, ))
		elif info.scheme != "http":
			raise ValueError(info.scheme)
		
		port = info.port and int(info.port) or getservbyname(info.scheme)
		
		self.__base = info.path or ""
		#if not self.__base.endswith("/"):
		#	self.__base += "/"
			
		if not username:
			username = info.username

		if not headers:
			headers = {}
			
		
			
		headers.setdefault("Accept", "*/*")
		headers["Accept-Encoding"] = "identity"
		
		if username:
			password = password or info.password or ""
			headers["Authorization"] = "Basic " + b64encode("%s:%s" % (username, password))
			
		self.__headers = headers
		
		if not connection_manager:
			#from SimpleConnectionManager import SimpleConnectionManager as connection_manager
			from ConnectionPoolManager import ConnectionPoolManager as connection_manager
			
		self.__connection_manager = connection_manager(host = info.hostname, port = port, 
						certfile = certfile, keyfile = keyfile, force_ssl = info.scheme == "https")
		
	def request(self, method, path, data = None, headers = {}, args = None):
		if isinstance(data, unicode):
			data = data.encode("utf-8")
		fullpath = self.__base + path	 
		request_headers = self.__headers.copy()
		
		if args:
			fullpath += ("?" in fullpath and "&" or "?") + compose_qs(args)
		
		if headers:
			request_headers.update(headers)

		if method == "GET":
			timeout = self.get_timeout
			try:
				etag, modified, cached = self.__cache[fullpath]
				if etag:
					request_headers["If-None-Match"] = etag
				request_headers["If-Modified-Since"] = modified
			except KeyError:
				request_headers.pop("If-None-Match", None)
				request_headers.pop("If-Modified-Since", None)
		else:
			timeout = self.timeout
			request_headers.setdefault("Content-Type", self.__content_type)
			
		log_headers = request_headers
		if self.logger.isEnabledFor(DEBUG) and "Authorization" in request_headers:
			log_headers = request_headers.copy()
			log_headers["Authorization"] = "<purged>"
		
		if method == "GET":
			self.logger.debug("%s: %s (%s)", method, fullpath, log_headers)
		else:
			self.logger.debug("%s: %s (%s)\n%s", method, fullpath, log_headers, repr(data))
		
		t = time()
		try:
			response = self.__connection_manager.request(method, fullpath, data, request_headers, timeout)
		except Exception, e:
			if self.logger.isEnabledFor(DEBUG):
				self.logger.exception("Error during request")
			if str(e) in ("", "''"):
				e = repr(e)
			try:
				error_msg = "An error occurred while contacting the %s: %s. Request was: %s %s (%.4fs)" % (self.component_name, e, method, fullpath, time() - t)
			except:
				self.logger.exception("Failed to format error message.")
				error_msg = "Error during request."
				
			raise CommunicationError(error_msg)
		
		logger.debug("%s %s result: %s (%.4fs)", method, fullpath, response.status, time() - t)
		if response.status == 304:
			response.close()
			try:
				self.logger.debug("Using cached answer for %s (%s, %s):\n %s", fullpath, etag, modified, cached)
				return closing(StringIO(cached))
			except NameError:
				raise CommunicationError("Error: The %s returned 304 though no cached version is available. Request was: %s %s" % (self.component_name, method, fullpath))
		if response.status == 302:
			raise NotImplementedError("HTTP redirect")
		if response.status < 200 or response.status >= 300:
			with response:
				via = response.getheader("Via")
				try:
					data = response.read(self.ERROR_RESPONSE_MAX and self.ERROR_RESPONSE_MAX + 1 or None)
					if not data or (not self.logger.isEnabledFor(DEBUG) and "<html>" in data):
						data = "<no further information available>"
					else:
						if self.ERROR_RESPONSE_MAX and len(data) > self.ERROR_RESPONSE_MAX:
							data  = data[:self.ERROR_RESPONSE_MAX] + " (truncated)\n"
						data = data.encode("utf-8")  
				except Exception, e:
					data = u"<failed to read error response: %s>" % (e, )

			if not data.endswith("\n"):
				data += "\n"
				
			try:
				msg = "Error during execution. The %s said: %s %s - %sRequest was: %s %s. " % (self.component_name, response.status, response.reason, data, method, fullpath)
			except:
				msg = "Error during execution. The %s said %s. " % (self.component_name, response.status)
			
			if via:
				culprit = via.split(",")[0]
				p = culprit.rfind("(")
				if p >= 0 and culprit.endswith(")"):
					culprit = culprit[p + 1:-1]
				msg += "The error occurred after the request went through %s (Via: %s)." % (culprit, via)
			else:
				msg += "The error seems to have occurred at the %s (No Via header found in response)." % (self.component_name, )
			
			#self.logger.error(msg)
			raise RemoteError(msg, code = response.status)  
		
		if method == "DELETE":
			self.__cache.pop(fullpath, None)
		else:
			etag = response.getheader("Etag")
			modified = response.getheader("Last-Modified")
			if etag or modified:
				if not modified:
					modified = datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
				response = CachingHttplibResponseWrapper(response, fullpath, etag, modified, self.__cache)
			elif self.logger.isEnabledFor(DEBUG):
				response = LoggingResponseWrapper(response)

		return response

	def get(self, path, headers = None, args = None):
		return self.request("GET", path, headers = headers, args = args)

	def post(self, path, data, headers = None):
		return self.request("POST", path, data, headers)
	add = post

	def put(self, path, payload, headers = None):
		return self.request("PUT", path, payload)
	update = put
		
	def delete(self, path, headers = None):
		self.request("DELETE", path, None, headers)
