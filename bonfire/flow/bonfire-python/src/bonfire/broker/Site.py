'''
Created on 24.11.2010

@author: kca
'''
from BrokerEntity import BrokerEntity
import re
from bonfire.broker.exc import NotFound, BrokerError

class Site(BrokerEntity):
	def get_reservations(self):
		return self.broker.get_reservations(self, user = self._user)
	reservations = property(get_reservations)
	
	def get_vm_images(self):
		return self.broker.get_vm_images(self, user = self._user)
	vm_images = property(get_vm_images)
	
	def get_storages(self, private = None):
		storages = self.broker.get_storages(self, user = self._user)
		if private:
			storages = [ s for s in self.broker.prefetch(storages) if s.public == False ]
		return storages
	storages = property(get_storages)
	
	def get_instance_types(self):
		if self.has_computes:
			return self.broker.get_instance_types(self, user = self._user)
		return [ "<n/a>" ]
	instance_types = property(get_instance_types)
	
	def get_computes(self):
		return self.broker.get_computes(self, user = self._user)
	computes = property(get_computes)
	
	def get_networks(self):
		return self.broker.get_networks(self, experiment = "bloodyhack", user = self._user)
	networks = property(get_networks)
	
	def get_datablocks(self, private = None):
		return self.broker.get_datablocks(self, experiment = "bloodyhack", user = self._user)
	datablocks = property(get_datablocks)
	
	def get_routers(self):
		return self.broker.get_routers(self, user = self._user)
	routers = property(get_routers)
	
	def get_physical_routers(self):
		return self.broker.get_physical_routers(self, user = self._user)
	physical_routers = property(get_physical_routers)
	
	def get_sitelinks(self):
		return self.broker.get_sitelinks(self, user = self._user)
	sitelinks = property(get_routers)
	
	def get_federicanetworks(self):
		return self.broker.get_federicanetworks(self, user = self._user)
	federicanetworks = property(get_federicanetworks)
	
	def get_services(self):
		return self.broker.get_services(self, user = self._user)
	services = property(get_services)
	
	def get_service(self, name):
		for s in self.services:
			if s.name == name:
				return s
		raise NotFound("%s has no service named %s" % (self.name, name))
	
	@property
	def aggregator_ip(self):
		try:
			return self.get_service("aggregator").ip
		except NotFound:
			return None
	
	def get_configurations(self):
		return self.broker.get_configurations(self, self._user)

	def get_elasticity_image(self):
		return self.get_image(self.broker.elasticity_image_name)
	
	def get_aggregator_image(self):
		return self.get_image(self.broker.aggregator_image_name)
	
	def get_versioned_image(self, name):
		pattern = r"BonFIRE %s(?:\s+v(\d+))?" % (name, )
		return self.get_image(pattern)

	def get_image(self, name):
		pattern = re.compile(name, re.I)

		aggimage = None
		candidates = []
		versions = {}

		for image in self.broker.get_storages(location = self, user = self._user):
			try:
				v = int(pattern.match(image.name).group(1))
			except (TypeError, IndexError, ValueError):
				v = 0
			except AttributeError:
				continue
			
			candidates.append(image)
			versions[image.id] = v
			
		candidates = self.broker.prefetch(candidates)
		
		version = -1
		for image in candidates:
			v = versions[image.id]
			if v > version and image.is_os_image:
				self.logger.debug("Preferring %s over %s (%d > %d)" % (image.name, aggimage and aggimage.name or aggimage, v, version))
				aggimage = image
				version = v

		return aggimage
		
	def get_wan(self):
		for network in self.networks:
			if network.is_wan:
				return network
		return None
	
	def get_default_network(self):
		if self.is_cells:
			for network in self.networks:
				if network.name.lower() == "internet@hp":
					return network
			return None
		return self.get_wan()
	
	def get_default_networks(self):
		wan = self.get_wan()
		networks = wan and [ wan ] or []
		
		if self.is_cells:
			for network in self.networks:
				if network.name.lower() == "internet@hp":
					return [ network ] + networks
				
		return networks
					
	
	@property
	def is_aggregator_capable(self):
		return not self.is_aws and self.get_default_network() is not None and self.get_aggregator_image() is not None
	
	@property
	def is_elasticity_capable(self):
		return self.is_one and self.get_elasticity_image() is not None
	
	@property
	def is_vw(self):
		return self.type == "VW"
	
	@property
	def is_cells(self):
		return self.type == "CELLS"
	
	@property
	def has_computes(self):
		# signifies a none compute site
		return self.supports_type("compute")
	
	@property
	def is_aws(self):
		return self.name.lower().endswith("-aws") or self.type == "AWS"
	is_amazon = is_aws
	
	@property	
	def is_federica(self):
		return self.name.lower() == "federica" or self.type == "FEDERICA"
	
	@property
	def is_autobahn(self):
		return self.name.lower() == "autobahn" or self.type == "AUTOBAHN"
	
	@property
	def is_one(self):
		return self.type == "ONE" or (not self.is_vw and not self.is_cells and not self.is_aws and not self.is_federica and not self.is_autobahn)
	
	@property
	def is_inria(self):
		return self.url.endswith("/fr-inria")
	
	@property
	def reservations_url(self):
		if self.name == "fr-inria":
			return self.url + "/reservations"
	
	@property
	def type(self):
		return self.site_info.get("type", "ONE").upper()
	
	@property
	def ssh_gateway(self):
		return self.site_info.get("ssh_gateway") or None
	
	@property
	def is_autobahn_endpoint(self):
		return bool(self.site_info.get("is_autobahn_endpoint"))
	
	@property
	def is_federica_endpoint(self):
		return bool(self.site_info.get("is_federica_endpoint"))

	@property
	def site_info(self):
		return self.broker.get_site_info(self)
	
	@property
	def account(self):
		return self.broker.get_account(self, user =  self._user)
	
	@property
	def default_network_name(self):
		if self.is_cells:
			return "Internet@HP"
		return self._broker.wan_name
	
	def supports_type(self, type):
		if type in ("compute", "storage"):
			return not (self.is_autobahn or self.is_federica)
		if type == "network":
			return not (self.is_autobahn or self.is_federica or self.is_aws)
		if type == "sitelink":
			return self.is_autobahn
		if type in ("router", "physical_router", "federicanetwork"):
			return self.is_federica
		raise BrokerError("Not a resource type: %s" % (type, ))
	
	@property
	def supports_livemigration(self):
		return self.is_one

class Service(BrokerEntity):
	__fields__ = (
		("ip", str),
	)
