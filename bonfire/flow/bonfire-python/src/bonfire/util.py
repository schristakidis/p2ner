'''
Created on 14.07.2011

@author: kca
'''

from socket import socket as _socket, AF_INET, SOCK_STREAM, error
from contextlib import closing
from collections import namedtuple

def errorstr(e):
	try:
		message = e.message
	except AttributeError:
		message = str(e)
	else:
		if not message:
			message = repr(e)
	return message

class TestResult(namedtuple("TestResult", ("result", "message"))):
	def __new__(cls, result, message = ""):
		return super(TestResult, cls).__new__(cls, result, message)
		
	def __bool__(self):
		return self.result
	__nonzero__ = __bool__
	
	def __str__(self):
		if self.message:
			return "%s - %s" % (self.result and "OK" or "Not active", self.message)
		return self.result and "OK" or "Not active"

def socket(family = AF_INET, type = SOCK_STREAM, proto = 0):
	return closing(_socket(family, type, proto))

def test_port(host, port, family = AF_INET, type = SOCK_STREAM, expect = None, timeout = None):
	try:
		with socket(family, type) as s:
			if timeout:
				s.settimeout(timeout)
			s.connect((host, port))
			if expect:
				r = s.read(len(expect))
				if r != expect:
					return TestResult(False, "Unexpected reply: %s" % (r, ))
	except error, e:
		return TestResult(False, "%s (%s)" % (e.strerror, e.errno))
	except Exception, e:
		return TestResult(False, errorstr(e))
	return TestResult(True)
		
from asyncore import dispatcher, loop
import sys
from time import time

class PortTester(dispatcher):
	result = TestResult(False, "Test did not run")
	EXPECT = "SSH"
	
	def __init__(self, host, port, family = AF_INET, type = SOCK_STREAM, map = None):
		dispatcher.__init__(self, map = map)
		self.create_socket(family, type)
		self.connect((host, port))
		self.port = port

	def handle_connect(self):
		self.result = TestResult(False, "Did not receive a reply")
		self.__read = ""
		
	def handle_read(self):
		self.__read += self.recv(len(self.EXPECT) - len(self.__read))
		if self.__read:
			if self.__read.lower() != self.EXPECT[:len(self.__read)].lower():
				self.result = TestResult(False, "Unexpected reply: %s" % (self.__read, ))
			elif len(self.__read) == len(self.EXPECT):
				self.result = TestResult(True)
			else:
				return
			
		self.close()

	def handle_error(self):
		self.result = TestResult(False, errorstr(sys.exc_value))
		self.close()
	
def run_test(map, timeout = 0.0):
	if timeout and timeout > 0.0:
		timeout = float(timeout)
		start = time()
		#realstart = time()
		while True:
			loop(map = map, timeout = timeout, count = 1)
			if map:
				now = time()
				timeout -= now - start
				if timeout <= 0.0:
					for r in map.itervalues():
						r.result = TestResult(False, "Timeout")
					break
				start = now
			else:
				break
		#print("Port test finished in %ss" % (time() - realstart, ))
	else:
		loop(map = map)
		
try:
	from collections import OrderedDict
except ImportError:
	#Fallback for python <2.7
	from ordereddict import OrderedDict
		
class LRUCache(OrderedDict):
	def __init__(self, max_items = 100, threadsafe = True, *args, **kw):
		super(LRUCache, self).__init__(*args, **kw)
		if max_items <= 0:
			raise ValueError(max_items)
		self.max_items = max_items
		if threadsafe:
			from threading import RLock
			self.__lock = RLock()
		else:
			self.__getitem__ = self._getitem
			self.__setitem__ = self._setitem
		
	def __getitem__(self, k):
		with self.__lock:
			return self._getitem(k)
		
	def get(self, k, default = None):
		try:
			return self[k]
		except KeyError:
			return default
		
	def _getitem(self, k):
		v = super(LRUCache, self).__getitem__(k)
		del self[k]
		super(LRUCache, self).__setitem__(k, v)
		return v
	
	def __iter__(self):
		for k in  tuple(super(LRUCache, self).__iter__()):
			yield k
	
	def __setitem__(self, k, v):
		with self.__lock:
			self._setitem(k, v)
		
	def _setitem(self, k, v):
		super(LRUCache, self).__setitem__(k, v)
		if len(self) > self.max_items:
			self.popitem(False)
			
from threading import Thread, Event
from Queue import Queue
import logging
			
class ThreadPool(object):
	def __init__(self, num_workers, *args, **kw):
		self._work_queue = Queue()
		[ Worker(self._work_queue).start() for _ in range(num_workers) ]
		
	def put(self, func, *args, **kw):
		self._work_queue.put((func, args, kw))
				
	def work(self, func, arglist):
		if arglist:
			count = [ len(arglist) ]
			done = Event()
			
			def counting_wrapper(*args, **kw):
				try:
					func(*args, **kw)
				finally:
					count[0] -= 1
					if count[0] <= 0:
						done.set()
				
			[ self._work_queue.put((counting_wrapper, args, kw)) for args, kw in arglist ]
			done.wait()			
	
class Worker(Thread):
	logger = logging.getLogger("bonfire.broker")
	
	def __init__(self, work_queue):
		Thread.__init__(self)
		self.daemon = True
		self.work_queue = work_queue
		
	def run(self):
		while True:
			func, args, kw = self.work_queue.get()
			try:
				func(*args, **kw)
			except:
				self.logger.exception("Internal Error")
				pass
