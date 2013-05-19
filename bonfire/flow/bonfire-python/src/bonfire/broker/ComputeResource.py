'''
Created on 24.11.2010

@author: kca
'''

from ..Entity import Attribute
from BrokerEntity import BasicBrokerEntity, BrokerEntity, DynamicReference
from Resource import Resource 
from StorageResource import StorageResource
from NetworkResource import NetworkResource
from bonfire.util import TestResult, errorstr, PortTester, run_test
from exc import TotallySurprisedError 
from bonfire.broker.exc import BrokerError
from operator import attrgetter
from time import sleep, time
from httplib import HTTPConnection
import socket

class Disk(BasicBrokerEntity):
	__fields__ = (
		("id", int),
		("storage", StorageResource),
		Attribute("type", str, "disk"),
		("target", str),
		("save_as", DynamicReference),
		("groups", str)
	)
	
	__ignore__ = ( "id", )
	
	def __init__(self, storage = None, *args, **kw):
		super(Disk, self).__init__(*args, **kw)
		if storage is not None:
			self.storage = storage
			
	#@property
	#def id(self):
	#	return "n/a"

class Nic(BasicBrokerEntity):
	__fields__ = (
		("network", NetworkResource),
		("ip", str),
		("mac", str),
	)

	def __init__(self, network = None, *args, **kw):
		super(Nic, self).__init__(*args, **kw)
		if network is not None:
			self.network = network 
			
	@property
	def id(self):
		return "n/a"
	
class Configuration(BrokerEntity):
	__fields__ = (
		("cpu", float),
		("memory", int),
	)
	
	@property
	def instance_type(self):
		return self.name
	
	@property
	def vcpu(self):
		return self.cpu
	
	@property
	def vmem(self):
		return self.memory
	
	@property
	def description(self):
		if not self.cpu or not self.memory:
			return "cpus: unknown, memory: unknown"
		return "cpus: %.2g, memory: %sMiB" % (self.cpu, self.memory)
		
	def __str__(self):
		return "%s (%s)" % (self.name, self.description)

class ComputeResource(Resource):
	#__fields__ = [ "network", "storage", "vmimage", "instance_type" ]
	__fields__ = (
		("instance_type", str),
		("cpu", float),
		("vcpu", int),
		("memory", int),
		("cluster", str),
		("migration_strategy", str),
		("host", str),
		("state", str),
		("disk", Disk),
		("nic", Nic),
	)
	
	__state_graph = {
		"running": ("suspended", "shutdown", "stopped", "cancel"),
		"active": ("suspended", "shutdown", "stopped", "cancel"),
		"on": ("suspended", "shutdown", "stopped", "cancel"),
		"up": ("suspended", "shutdown", "stopped", "cancel"),
		"stopped": ("resume", ),
		"suspended": ("resume", ),
	}
		
	def __init__(self, *args, **kw):
		super(ComputeResource, self).__init__(*args, **kw)
		self.__context = {}
		
	def get_context(self):
		return self.__context
	context = property(get_context)
	
	@property
	def is_active(self):
		return self.state.lower() in ("active", "running", "on", "up")
	active = is_active
	
	@property
	def is_failed(self):
		return self.state.lower().startswith("fail")
	failed = is_failed
	
	@property
	def is_pending(self):
		s = self.state.lower()
		return s in ("pending", "prolog") or s.startswith("boot")
	pending = is_pending
	
	@property
	def is_aggregator(self):
		try:
			return self.broker and self.broker.aggregator_name.lower() in self.name.lower()
		except BrokerError:
			return False
		
	@property
	def is_elasticity_engine(self):
		try:
			return self.broker and self.broker.elasticity_name.lower() in self.name.lower()
		except BrokerError:
			return False
	
	def set_context(self, name, value):
		self.__context[unicode(name)] = unicode(value) 
	
	@property	
	def available_states(self):
		return self.__state_graph.get(self.state.lower(), ())
	
	@property
	def system_disk(self):
		return self.disk and self.disk[0] or None
	
	@property
	def dnsname(self):
		if self.location.endswith("be-ibbt"):
			experiment = self.experiment
			if hasattr(experiment, "short_id"):
				experiment = experiment.short_id
			return "%s.bonfire-%s.BonFIRE.wall.test" % (self.name, experiment)
		if self.nic:
			return self.nic[0].ip
		return "n/a"
	
	@property
	def wan_nic(self):
		try:
			return self.__wan_nic
		except AttributeError:
			l = self._broker.get_site(self.location, self._user)
			if l.is_cells or l.is_aws:
				if self.nic:
					return self.nic[0]
			else:	
				for n in self.nic:
					if n.network.is_wan:
						self.__wan_nic = n
						return n
			raise TotallySurprisedError("Not connected to any WAN")
		
	def get_wan_ip(self):
		try:
			wn = self.wan_nic
		except TotallySurprisedError:
			return "<unassigned>"
		
		return wn.ip or "<unassigned>"
	wan_ip = property(get_wan_ip)
	
	def _naive_test(self):
		if not self.active:
			return TestResult(False, "Host is not active")
		try:
			wan = self.wan_nic
		except Exception, e:
			return TestResult(False, errorstr(e))
		
		if not wan.ip:
			return TestResult(False, "No IP assigned")
		return TestResult(True)
	
	def test_http(self, naive = False, path = "/", port = 80, method = "GET", timeout = 10):
		result = self._naive_test()
		
		if result and not naive:
			try:
				connection = HTTPConnection(self.wan_ip, port, timeout)
				try:
					connection.request(method, path)
					connection.getresponse().close()
				finally:
					connection.close()
			except socket.error, e:
				return TestResult(False, e[1])
			except Exception, e:
				return TestResult(False, errorstr(e))
		
			result = TestResult(True)
		
		return result
	
	@property
	def dnsname_only(self):
		if self.location.endswith("be-ibbt"):
			return "%s.bonfire-%s.BonFIRE.wall.test" % (self.name, self.experiment.short_id)
		return ""
	
	@staticmethod
	def test_wan_ports(computes, port, timeout = 10.0):
		result = {}
		tests = []
		map = {}
		for c in computes:
			try:
				r = c._naive_test()
			except BrokerError, e:
				result[c] = TestResult(False, str(e))
			else:
				if r:
					tests.append((c, PortTester(c.wan_nic.ip, port, map = map)))
				else:
					result[c] = r
					
		if tests:
			run_test(map = map, timeout = timeout)
			for c, t in tests:
				result[c] = t.result
					
		return result
	
	def get_configuration(self):
		if not self.instance_type:
			raise TotallySurprisedError("Instance type missing")
		return self._broker.get_configuration(self.location, self.instance_type, self._user)
	
	@property
	def storages(self):
		return self.disk and filter(None, map(attrgetter("storage"), self.disk)) or ()
	
	@property
	def networks(self):
		return self.nic and filter(None, map(attrgetter("network"), self.nic)) or ()
	
	def wait_for_active(self, timeout = 60, label = "Compute"):
		start = time()
		while not self.active:
			sleep(1)
			if time() - start > timeout:
				raise BrokerError("%s %s did not change to runnning within %s seconds." % (label, self.id, timeout))
			self.refresh()
