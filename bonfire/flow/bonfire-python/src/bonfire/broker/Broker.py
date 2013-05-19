'''
Created on 15.11.2010

@author: kca
'''

from bonfire.broker import logger
from exc import BrokerError, UnknownEntityType, BonfireError
from ..util import ThreadPool, OrderedDict
from time import sleep
from Account import Account 
from Experiment import Experiment
from ComputeResource import ComputeResource, Configuration
from NetworkResource import NetworkResource, DefaultNetworkResource, VirtualWallNetworkResource
from StorageResource import StorageResource
from Reservation import Reservation
from Site import Site, Service
from occi import OCCISerializer
from Resource import Resource
from BrokerEntity import BrokerEntity
import re
from threading import local
from bonfire.http.RestClient import RestClient
from bonfire.http.exc import RemoteError
from collections import namedtuple
from json import load
from bonfire.broker.occi.etree import Surprised
from urlparse import urlparse
from bonfire.broker.Experiment import Event
from federica import Router, PhysicalRouter
from Sitelink import Sitelink
from operator import attrgetter
from bonfire.broker.federica import FedericaNetwork
import threading

class DummyConfiguration(namedtuple("DummyConfigurationBase", ("name", ))): 
	@property
	def vmem(self):
		return None
	
	@property
	def vcpu(self):
		return None
	
	def __str__(self):
		return self.name
	
	@property
	def description(self):
		return ""

class Broker(object):	
	logger = logger
	grace_period = None
		
	SITES = {
		"de-hlrs": {
			"type": "ONE", 
			"ssh_gateway": "",
		},
		"uk-epcc": {
			"type": "ONE", 
			"ssh_gateway": "ssh.uk-epcc.bonfire-project.eu",
			"is_autobahn_endpoint": True,
			"is_federica_endpoint": True
		},
		"fr-inria": {
			"type": "ONE", 
			"ssh_gateway": "ssh.fr-inria.bonfire-project.eu",
		},
		"be-ibbt": {
			"type": "VW", 
			"ssh_gateway": "ssh.be-ibbt.bonfire-project.eu",
		},
		"uk-hplabs": {
			"type": "CELLS", 
			"ssh_gateway": "",
		},
		"pl-psnc": {
			"type": "ONE", 
			"is_autobahn_endpoint": True,
			"is_federica_endpoint": True
		},
		"autobahn": {
			"type": "AUTOBAHN"
		},
		"federica": {
			"type": "FEDERICA"
		}
	}
	
	__urlmap = {
			Site: "locations",
			StorageResource: "storages",
			Experiment: "experiments",
			NetworkResource: "networks",
			VirtualWallNetworkResource: "networks",
			DefaultNetworkResource: "networks",
			ComputeResource: "computes",
			Configuration: "configurations",
			Service: "services",
			Account: "account",
			Event: "events",
			Router: "routers",
			Sitelink: "site_links",
			PhysicalRouter: "physical_infrastructures",
			FedericaNetwork: "networks"
	}
	
	__typenames = {
			"storage": StorageResource,
			"network": DefaultNetworkResource,
			"federicanetwork": FedericaNetwork, 
			"compute": ComputeResource,
			"experiment": Experiment,
			"router": Router,
			"site_link": Sitelink,
			"sitelink": Sitelink
	}
	
	__xml_header = re.compile(r'<\?xml\s+version=".+?"\s+encoding="utf-8"\?>')
	
	def __init__(self, url, certfile = None, keyfile = None, schema = None,
				aggregator_image_name = None, aggregator_name = None, wan_name = None,
				site_info = None, timeout = None, get_timeout = None, num_threads = 16,
				grace_period = None, elasticity_name = None, elasticity_image_name = None,
				loadbalancer_image_name = None,
				username = None, password = None, *args, **kw):
		#super(Broker, self).__init__(*args, **kw)
		self.url = url
		self.__serializer = OCCISerializer(broker = self, schema = schema)
		self.__assume_user = None
		self.__local = local()
		self.aggregator_image_name = aggregator_image_name or r"BonFIRE Zabbix Aggregator(?:\s+v(\d+))?"
		self.elasticity_name = elasticity_name or "BonFIRE-Elasticity-Engine"
		self.elasticity_image_name = elasticity_image_name or r"BonFIRE Debian Squeeze 2G(?:\s+v(\d+))?"
		self.loadbalancer_image_name = loadbalancer_image_name or "Load Balancer 2G"
		#self.elasticity_image_name = elasticity_image_name or r"BonFIRE Elasticity Engine(?:\s+v(\d+))?"
		self.wan_name = wan_name or "BonFIRE WAN"
		self.__restclient = RestClient(url, certfile = certfile, keyfile = keyfile,
									content_type = "application/vnd.bonfire+xml", timeout = timeout,
									get_timeout = get_timeout, username = username, password = password)
		self.aggregator_name = aggregator_name or "BonFIRE-monitor"
		self.__threadpool = ThreadPool(num_threads)
		if site_info is not None:
			self.SITES = site_info
		if grace_period:
			self.grace_period = float(grace_period)
			
		self._aws_cache = {}
		self._aws_last_updated = 0
		self._site_cache = threading.local()
	
	def __do_request(self, method, path, user, data = None, experiment = None):
		user = user or self.__assume_user
		self.__local.user = user
		headers = user and {"X-Bonfire-Asserted-Id": str(user)} or {}
		if experiment:
			headers["X-BONFIRE-EXPERIMENT-ID"] = getattr(experiment, "url", experiment)
		return self.__restclient.request(method, path, data, headers)
	
	def _get_entity(self, data):
		url = data.href
		experiment = data.experiment
		name = data.name
		
		#if not url:
			#raise Exception(data.values)
		
		e = self.__make_entity(name, url, experiment, data)
		if issubclass(e.__class__, BrokerEntity):# MAD
			e._set_user(self.__local.user)
		return e
	
	def __make_entity(self, name, url, experiment, data):
		klass = data.entity_class
		if not issubclass(klass, BrokerEntity):
			return klass(xml = data.xml, broker = self, fields = data.values)
		e = BrokerEntity.__new__(klass)
		if issubclass(klass, Resource):
			Resource.__init__(e, name = name, url = url, xml = data.xml, location = data.location, experiment = experiment, broker = self, fields = data.values)
		elif issubclass(klass, Resource):# ??? how does this work?
			Resource.__init__(e, name = name, url = url, xml = data.xml, location = data.location, broker = self, fields = data.values)
		else:
			BrokerEntity.__init__(e, name = name, url = url, xml = data.xml, broker = self, fields = data.values)
		
		return e

	def __get_entities(self, klass, user, prefix = "", experiment = None):
		collection = self.__urlmap.get(klass, klass.__name__.lower() + "s")
		with self.__do_request("GET", prefix + "/" + collection, user, experiment = experiment) as xml:
			return self.__serializer.parse_collection(xml, klass)
	
	def _get_fields(self, e, user = None):
		if isinstance(e, Resource):
			return self._fetch_fields(e, e.experiment, user)
		return self._fetch_fields(e, None, user)
			
	def _fetch_fields(self, e, experiment, user):
		with self.__do_request("GET", e.url, user) as xml:
			return self.__serializer.parse_item_raw(xml, e.__class__, experiment)
	
	def __get_entity(self, klass, id, user, experiment):
		with self.__do_request("GET", id, user, experiment = experiment) as xml:
			data = self.__serializer.parse_item(xml, klass, experiment)
		return data
	
	def get_entity(self, klass, id, user = None, experiment = None):
		if isinstance(klass, basestring):
			klass = self.get_entity_class(klass)
		if klass in (NetworkResource, DefaultNetworkResource):
			if "/be-ibbt/" in id:
				klass = VirtualWallNetworkResource
			elif "/uk-hplabs/" in id:
				klass = NetworkResource
		return self.__get_entity(klass, id, str(user), experiment)
	
	def _get_resources(self, klass, location, user, experiment = None):
		if not isinstance(location, basestring):
			location = location.url
		elif not location.startswith("/locations/"):
			location = "/locations/" + location
		
		return self.__get_entities(klass, user, location, experiment = experiment)

	def get_sites(self, user = None):
		return self.__get_entities(Site, user)
	
	def get_sites_by_image(self, image, user):
		aggsites = []
		
		def _worker(site):
			try:
				if site.get_versioned_image(image) is not None:
					aggsites.append(site)
			except:
				self.logger.exception("Error while looking for image '%s' at %s" % (image, site.url, ))
				
		self.__threadpool.work(_worker, [ ((site, ), {}) for site in self.get_sites(user) ])
		return aggsites
	
	def get_aggregator_sites(self, user):
		aggsites = []
		
		def _worker(site):
			try:
				if site.is_aggregator_capable:
					aggsites.append(site)
			except:
				self.logger.exception("Error while looking for aggregator image at %s" % (site.url, ))
				
		self.__threadpool.work(_worker, [ ((site, ), {}) for site in self.get_sites(user) ])
		return aggsites
	
	def get_elasticity_sites(self, user):
		aggsites = []
		
		def _worker(site):
			try:
				if site.is_elasticity_capable:
					aggsites.append(site)
			except:
				self.logger.exception("Error while looking for EaaS image at %s" % (site.url, ))
				
		self.__threadpool.work(_worker, [ ((site, ), {}) for site in self.get_sites(user) ])
		return aggsites

	def get_site(self, id, user = None):
		if isinstance(id, Site):
			return id
		try:
			return getattr(self._site_cache, id)
		except AttributeError:
			site = self.__get_entity(Site, id, user, None)
			setattr(self._site_cache, id, site)
			return site
	
	def _get_site_storages(self, location, user = None, experiment = None):
		if location is None:
			return []		
		return self._get_resources(StorageResource, location, user, experiment = experiment)
	
	def _get_site_computes(self, location, user = None):
		if location is None:
			return []
		return self._get_resources(ComputeResource, location, user)
			
	def _get_site_networks(self, location, user = None):
		location = self.get_site(location, user)
		if location.is_vw:
			klass = VirtualWallNetworkResource
		elif location.is_cells:
			klass = NetworkResource
		else:
			klass = DefaultNetworkResource
		return self._get_resources(klass, location, user)
	
	def _refresh_aws(self, location, user):
		self._aws_cache = self.prefetch(self._get_site_storages(location, user))
	
	def get_vm_images(self, location, user = None, experiment = None):
		locurl = getattr(location, "url", location)
		
		if "aws" in locurl:
			return self.get_storages(location, user, experiment)
			
		storages = self.prefetch(self._get_site_storages(location, user, experiment = experiment))
		return [ s for s in storages if not s.is_datablock ]
	
	def get_datablocks(self, location, experiment = None, user = None):
		locurl = getattr(location, "url", location)
		
		if "aws" in locurl:
			return []
		
		storages = self.prefetch(self._get_site_storages(location, user))
		if experiment:
			experiment = getattr(experiment, "url", experiment)
			storages = [ r for r in storages if r.experiment == experiment or not r.experiment ]
		return [ s for s in storages if s.is_datablock ]
	
	def get_storages(self, location = None, user = None, experiment = None):
		if location:
			return self._get_site_storages(location, user, experiment = experiment)
		return self._collect_site_resources("storages", location, user, self.get_sites(user))
	
	def get_computes(self, location = None, user = None):
		if location:
			return self._get_site_computes(location, user)
		return self._collect_site_resources("computes", location, user, self.get_sites(user))
	
	def get_networks(self, location = None, experiment = None, user = None):
		if location:
			networks = self._get_site_networks(location, user)
			if experiment:
				experiment = getattr(experiment, "url", experiment)
				networks = [ r for r in self.prefetch(networks) if r.experiment == experiment or not r.experiment ]
			return networks
		return self._collect_site_resources("networks", location, user, self.get_sites(user))
	
	def get_routers(self, location, user = None):
		if location:
			return self._get_resources(Router, location, user)
		return self._collect_site_resources("routers", location, user, self.get_sites(user))

	def get_federica_physical_routers(self, location, user = None):
		if location:
			return self._get_resources(PhysicalRouter, location, user)
		return self._collect_site_resources("physical_routers", location, user, self.get_sites(user))
	get_physical_routers = get_federica_physical_routers
	
	def get_federica_networks(self, location, experiment = None, user = None):
		if location:
			return self._get_resources(FedericaNetwork, location, user, experiment)
		return self._collect_site_resources("federicanetworks", location, user, self.get_sites(user))
	get_federicanetworks = get_federica_networks
	
	def get_services(self, location, user = None):
		return self._get_resources(Service, location, user)
	
	def get_events(self, experiment, user = None):
		experiment = getattr(experiment, "url", experiment)
		return self.__get_entities(Event, user, prefix = experiment)
	
	def get_raw_events(self, experiment, user = None):
		experiment = getattr(experiment, "url", experiment)
		with self.__do_request("GET", experiment + "/" + "events", user) as xml:
			return xml.read()
	
	def _collect_site_resources(self, type, location, user, sites):
		def _worker(s, type):
			try:
				result.extend(getattr(s, type))
			except BonfireError, e:
				self.logger.warning("Error adding %s for site %s: %s" % (type, str(s), e))
				
		result = []
		self.__threadpool.work(_worker, [ ((s, type), {}) for s in sites if not s.is_aws and s.supports_type(type[:-1]) ])
		return result
		
	def get_instance_types(self, location, user = None):
		return [ c.name for c in self.get_configurations(location, user) ]
	
	
	
	def get_experiments(self, user = None, user_id = None):	
		experiments = self.__get_entities(Experiment, user)
		if user_id:
			experiments = [ e for e in experiments if e.user_id == user_id ]
		return experiments
	
	def get_experiment(self, id, user = None):
		if isinstance(id, Experiment):
			return id
		return self.__get_entity(Experiment, id, user, None)
	
	def get_configurations(self, location, user = None, experiment = None):
		configs =  self._get_resources(Configuration, location, user, experiment)
		sorted = []
		custom = None
		for c in configs:
			if c.name.lower() == "custom":
				custom = c
			else:
				sorted.append(c)
		if custom:
			sorted.append(custom)
			configs = sorted
		return configs
		
	def get_configuration(self, location, name, user = None):
		configurations = self.get_configurations(location, user)
		for c in configurations:
			if c.name == name:
				return c
		raise BrokerError("No such configuration at %s: %s" % (hasattr(location, "url") and location.url or location, name))
	
	def get_account(self, site, user = None):
		site = self.get_site(site, user)
		return self.__get_entity(Account, site.url + "/account", user, None)
	
	def _load_json(self, json):
		try:
			return load(json)
		except (TypeError, ValueError):
			raise Surprised("Broker did not return valid json.")
		
	def _get_reservation_details(self, reservation, user):
		with self.__do_request("GET", reservation.url, user) as json:
			details = self._load_json(json)
			
		try:
			return {"cores": tuple(set(details["resources_by_type"]["cores"]))}
		except KeyError:
			return {"cores": ()}
	
	def get_reservations(self, site, user = None):
		site = self.get_site(site, user)
		if not site.is_inria:
			return []

		try:
			with self.__do_request("GET", site.url + "/reservations", user) as json:
				try:
					items = self._load_json(json)["items"]
				except KeyError:
					raise Surprised("'items' missing in json.")
		except RemoteError:
			self.logger.exception("Failed to get reservations for %s" % (site.id, ))
			return []
		
		reservations = []
		try:
			for i in items:
				try:
					fields = {}
					name = i["name"]
					for k in ("state", "uid"):
						fields[k] = i[k] 
					
					url = None
					for link in i["links"]:
						if link.get("rel") == "self":
							url = link.get("href")
							break
					if not url:
						raise KeyError("url")
					
					try:
						url = urlparse(url).path
					except Exception, e:
						raise Surprised("Failed to parse reservation URL: %s" % (url, )) 
					
					reservations.append(Reservation(url = url, name = name, broker = self, user = user, fields = fields))					
				except KeyError, e:
					self.logger.error("Error parsing reservations: '%s' missing in reservation entry: %s" % (e, i, ))
		except TypeError:
			self.logger.exception("Error parsing reservations")
			raise Surprised("Error parsing reservations: 'items' is not a list")
			
		return reservations
		
	def validate_occi(self, data):
		self.__serializer.validate(data)
	
	def occi(self, method, path, occi, user = None, validate = True, experiment = None):	
		if not path:
			raise ValueError(path)
		data = self.__xml_header.sub("", occi).strip(" \t\n")
		if path[0] != "/":
			path = "/" + path
		
		if validate:
			self.validate_occi(data)
		
		if not data.startswith("<?"):
			data = '<?xml version="1.0" encoding="UTF-8"?>\n' + data

		with self.__do_request(method, path, user, data, experiment = experiment) as _result:
			_result = self.__serializer.parse_response(_result)

		logger.debug("answer: %s" % (_result, ))
		
		if self.grace_period and path.endswith(("storages", "networks")):
			sleep(self.grace_period)
		
		return _result
	
	def delete(self, url, user = None):
		url = getattr(url, "url", url)
		url = url.replace("site/link", "site_link")# hack: the id for site_links is corrupted by the javascript
		self.__do_request("DELETE", url, user).close()
	delete_entity = delete
	
	def get_site_info(self, site):
		site = getattr(site, "name", site)
		return self.SITES.get(site, {})	
	
	def get_autobahn_endpoints(self, user = None):
		return filter(attrgetter("is_autobahn_endpoint"), self.get_sites(user = user))
	
	def _handle_prefetch_error(self, e, r, resources):
		self.logger.exception("Error prefetching %s." % (r.url, ))
		del resources[r.url]
	
	def _prefetch(self, r, resources, error_handler):
		try:
			r.refresh()
		except BonfireError, e:
			error_handler(e, r, resources)
	
	def prefetch_dict(self, resources, error_handler = None):
		result = OrderedDict([ (r.url, r) for r in resources ])
		
		work = []
		for r in resources:
			if r.needs_prefetching():
				work.append( ((r, result, error_handler or self._handle_prefetch_error), {}) )
		
		self.__threadpool.work(self._prefetch, work)
		return result
		
	def prefetch(self, resources, error_handler = None):
		return self.prefetch_dict(resources, error_handler).values()
	
	def get_entity_class(self, typename):
		try:
			return self.__typenames[typename.lower()]
		except KeyError:
			raise UnknownEntityType(typename)

# TODO get_sitelinks
	def get_sitelinks(self, user = None, user_id = None, location = None):
		return self.__get_entities(Sitelink, user, location or "/locations/autobahn")
