'''
Created on 08.05.2011

@author: kca
'''

from bonfire.broker import logger
from abc import ABCMeta, abstractmethod
from bonfire.broker.exc import OCCIError
from bonfire.broker import Site, VirtualWallNetworkResource, DefaultNetworkResource, NetworkResource, Sitelink
from bonfire.broker.federica import PhysicalRouter, FedericaNetwork
#from bonfire.authz import GroupInfo

try:
	from lxml import etree
	from lxml.etree import DocumentInvalid, XMLSyntaxError
except ImportError:
	logger.debug("lxml module not found. XML validation is disabled.")
	etree = None
else:
	from StringIO import StringIO

class AbstractSerializer(object):
	__metaclass__ = ABCMeta
	
	logger = logger
	
	def __init__(self, broker, schema = None, *args, **kw):
		super(AbstractSerializer, self).__init__(*args, **kw)
		self.__broker = broker
#		if broker.__class__.__name__ is not "Broker":
#			raise AttributeError("What are You doing Madam/Sir? %s" % broker.__class__)

		if etree is not None and schema is not None:
			xmlschema_doc = etree.parse(schema)
			self.__xmlschema = etree.XMLSchema(xmlschema_doc)
		else:
			self.__xmlschema = None
			
	@abstractmethod
	def parse_item_raw(self, xml, expect=None, experiment=None):
		raise NotImplementedError()
	
	@abstractmethod
	def parse_collection(self, xml, expect=None, experiment=None):
		raise NotImplementedError()
		
	@abstractmethod
	def parse_response(self, response):
		raise NotImplementedError()
	
	if etree is None:
		def validate(self, xml):
			pass
	else:
		def validate(self, xml):
			self.logger.debug("Validating: %s" % (xml,))
			try:
				doc = etree.parse(StringIO(xml))
				self.__xmlschema.assertValid(doc)
				self.logger.debug("XML validation success")
			except (XMLSyntaxError, DocumentInvalid), e:
				raise OCCIError("Error validating OCCI XML: " + str(e)) 
			
	def parse_item(self, xml, expect=None, experiment=None):
		d = self.parse_item_raw(xml, expect, experiment)
		return self._broker._get_entity(d)
		
	@property
	def _broker(self):
		return self.__broker
	
	def _get_tagname(self, klass):
		#self.logger.debug(klass.__name__)
		if issubclass(klass, (NetworkResource, DefaultNetworkResource ,VirtualWallNetworkResource, FedericaNetwork)):
			return "network"
		# GroupInfo -> groupInfo  & UsageInfo -> usageInfo
		# strcmp to circumvent cyclic import issue
		if klass.__name__ == "GroupInfo":
			return "groupInfo"
		if klass.__name__ == "UsageInfo":
			return "usageInfo"
		if klass is Sitelink:
			return "site_link"
		if klass is PhysicalRouter:
			return "physical_router"
		if klass.__name__.endswith("Resource"):
			return klass.__name__[:-8].lower()
		if klass is Site:
			return "location"
		return klass.__name__.lower()
	
