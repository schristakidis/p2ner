'''
Created on 15.11.2010

@author: kca
'''

from BrokerEntity import BrokerEntity, BasicBrokerEntity
from ComputeResource import ComputeResource
from StorageResource import StorageResource
from NetworkResource import NetworkResource
from Sitelink import Sitelink
from federica import Router
from iso8601 import parse_date
from datetime import timedelta
from operator import attrgetter
from bonfire.broker.federica import FedericaNetwork

class Event(BasicBrokerEntity):
	__fields__ = (
		("experiment_id", str),
		("kind", str),
		("status", str),
		("path", str),
		("timestamp", str)
	)
	
	@property
	def id(self):
		return self.timestamp
	
class EventsHelper(object):
	def __init__(self, events, *args, **kw):
		super(EventsHelper, self).__init__(*args, **kw)
		self.events = events

class Experiment(BrokerEntity):
	'''
	classdocs
	'''
		
	__fields__ = (
			("description", unicode),
			("walltime", int),
			("user_id", str),
			("status", str),
			("created_at", str),
			("updated_at", str),
			("user_id", str),
			("aggregator_password", str),
			("aws_access_key_id", str),
			("aws_secret_access_key", str),
			("networks", [ NetworkResource ]),
			("computes", [ ComputeResource ]),
			("storages", [ StorageResource ]),
			("site_links", [ Sitelink ]),
			("routers", [ Router ]),
	)
	
	__ignore__ = ("computes", "storages", "networks", "site_links")
	
	@property
	def sitelinks(self):
		return self.site_links
	
	@property
	def federicanetworks(self):
		return [ n for n in self.networks if isinstance(n, FedericaNetwork)]
	
	@property
	def real_networks(self):
		return [ n for n in self.networks if not isinstance(n, FedericaNetwork)]
	
	def get_aggregator(self):
		for c in self.computes:
			if c.is_aggregator:
				return c
	
	def get_elasticity_engine(self):
		for c in self.computes:
			if c.is_elasticity_engine:
				return c
	
	def get_aggregators(self):
		return [ c for c in self.computes if c.is_aggregator ]
	
	def get_elasticity_engines(self):
		return [ c for c in self.computes if c.is_elasticity_engine ]
	
	@property
	def locked(self):
		return self.stopped or self.cancelled
	
	@property
	def stopped(self):
		return self.status.lower() ==  "stopped"
	
	@property
	def cancelled(self):
		return self.status.lower().startswith("cancel") or self.status.lower() == "terminated"
	
	@property
	def waiting(self):
		return self.status.lower() == "ready"
	
	@property
	def running(self):
		return not self.waiting and not self.locked
		
	def get_capable_sites(self):
		if self.cancelled:
			return ()
		sites = self.broker.get_sites(self._user)
		if self.running:
			sites = [ site for site in sites if not (site.is_vw or site.is_federica) ]
		return tuple(sites)
	capable_sites = property(get_capable_sites)
	
	def get_available_networks(self, location = None):
		networks = self.real_networks
		if location:
			if hasattr(location, "url"):
				location = location.url
			networks = [ n for n in networks if n.location == location ]
		return list(set(networks + self.broker.get_networks(location = location, experiment = self, user = self._user)))
	
	def get_available_datablocks(self, location):
		storages = self.storages
		if location:
			if hasattr(location, "url"):
				location = location.url
			storages = [ n for n in storages if n.location == location ]
		return list(set(storages + self.broker.get_datablocks(location = location, experiment = self, user = self._user)))
	
	def get_active_routers(self):
		return self.get_routers("is_active")
		#return self.routers and filter(attrgetter("is_active"), self.routers) or []
	
	def get_routers(self, attr):
		"""
			@param attr: string property or field  name for filtering
			@return list of the experiment's routers, filtered by attr
		"""
		if not attr:
			return self.routers or []
		return self.routers and filter(attrgetter(attr), self.routers) or []

	def test_ssh(self, timeout = 3.0):
		return ComputeResource.test_wan_ports(self.computes, 22, timeout = timeout)
	
	@property
	def create_time(self):
		return self.created_at and parse_date(self.created_at) or None
	
	@property
	def update_time(self):
		return self.updated_at and parse_date(self.updated_at) or None
	
	@property
	def remaining_time(self):
		return timedelta(seconds = self.walltime)
	
	@property
	def expiry_time(self):
		t = self.create_time
		if t:
			t += self.remaining_time
		return t 
		
	@property
	def computes_url(self):
		return self.url + "/computes"
	
	@property
	def storages_url(self):
		return self.url + "/storages"
	
	@property
	def networks_url(self):
		return self.url + "/networks"
	
	@property
	def is_aws_enabled(self):
		return bool(self.aws_access_key_id)
	