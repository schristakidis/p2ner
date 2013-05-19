'''
Created on 08.05.2011

@author: kca
'''
from bonfire.broker import logger, Disk, NetworkResource, VirtualWallNetworkResource, Resource, DefaultNetworkResource
from bonfire.broker.Sitelink import AutobahnEndpoint
from bonfire.broker.federica import PhysicalNode, PhysicalRouter, FedericaNetwork
from bonfire.broker.EntityData import EntityData
from bonfire.broker.exc import TotallySurprisedError, IllegalFieldType
from bonfire.broker.BrokerEntity import BasicBrokerEntity, BrokerEntity, DynamicReference
from bonfire.broker.Experiment import Experiment, Event

try:
	from lxml.etree import ElementTree, XMLSyntaxError as ParseError, tostring as _ts, SubElement, Element, QName, XML, parse, LXML_VERSION
	ETREE_VERSION = '.'.join(map(str, LXML_VERSION))
	def tostring(element, pretty_print = False):
		return _ts(element, encoding = "utf-8", pretty_print = pretty_print)
except ImportError:
	logger.debug("lxml library not found. Trying builtin xml.etree.")
	from xml.etree.ElementTree import ElementTree, tostring as _ts, SubElement, Element, QName, XML, parse, VERSION as ETREE_VERSION

	try:
		from xml.etree.ElementTree import ParseError
	except ImportError:
		# < python 2.7
		from xml.parsers.expat import ExpatError as ParseError
		
	def tostring(element, pretty_print = False):
		return _ts(element, encoding = "utf-8")
	
from AbstractSerializer import AbstractSerializer

class Surprised(TotallySurprisedError):
	def __init__(self, msg, xml = None, *args, **kw):
		super(Surprised, self).__init__(xml is not None and ("%s %s" % (msg, tostring(xml))) or msg, *args, **kw)
		
class OCCISerializer(AbstractSerializer):
	XMLNS = "http://api.bonfire-project.eu/doc/schemas/occi"
	
	def parse_item_raw(self, xml, expect = None, experiment = None):
		#self.logger.debug(xml.read())
		return self.__parse_node_checked(self.__parse(xml), expect, 1, experiment)
			
	def parse_collection(self, xml, expect = None, experiment = None):
		doc = self.__parse(xml)
		
		root = doc
		if expect is Event:
			if doc.tag != "events":
				raise Surprised(msg = " \"events\" node not found in doc.", xml = doc)
		elif expect in (PhysicalRouter, PhysicalNode):
			if doc.tag != self.__qn("physical_infrastructure"):
				raise Surprised(msg = " \"physical_infrastructure\" node not found in doc.", xml = doc)
		else:
			root = doc.find(self.__qn("items"))
			if root is None:
				raise Surprised(msg = " \"items\" node not found in doc.", xml = doc)
		
		return self.__parse_inner_collection(root, expect, experiment)

	def parse_response(self, response):
		if response:
			return self.__parse(response).get("href")
		
	def pretty_print(self, buffer):
		return tostring(ElementTree().parse(buffer))
		
	def _get_tagnames(self, klass):
		tagname = super(OCCISerializer, self)._get_tagname(klass)
		return tagname, self.__qn(tagname)
			
	def __parse(self, buffer):
		try:
			return ElementTree().parse(buffer)
		except ParseError, e:
			raise Surprised("Error parsing OCCI: %s" % (e, ))
		
	def __parse_node_checked(self, node, expect, i, experiment = None):
		if expect and node.tag not in self._get_tagnames(expect):
			raise Surprised("Unexpected element in xml: %s. Expected %s." % (node.tag, self._get_tagname(expect)), node)
		return self.__parse_node(node, expect, i, experiment)
			
	def __parse_node(self, node, expect, i, experiment = None):
		if expect is None:
			expect = self._broker.get_entity_class(node.tag.rsplit("}", 1)[-1])

		if issubclass(expect, BrokerEntity):
			name = node.get("name")
			href = node.get("href")
			
			if not href:
				raise Surprised("href missing", node)
			
			if not name:
				name = node.findtext(self.__qn("name"))
				if not name:
					if href.startswith("/locations/"):
						parts = href.split("/")
						if len(parts) == 3:
							name = parts[-1]
					if not name: 
						#be tolerant towards federica resources (#1081)
						if href.startswith("/locations/federica/router"):
							name = "_see_bug_#1081_"
						else:
							raise Exception(str(Surprised("name missing" + str(expect), node)))
			
			name = name.strip(" \n\t")
			location = '/'.join(href.split("/", 3)[:3])
		else:
			name = href = location = None
		
		if len(node):
			fields = expect.get_fields()
			values = {}
			if not experiment and issubclass(expect, Resource):
				for link in node.findall(self.__qn("link")):
					if link.get("rel") == "experiment":
						experiment = link.get("href")
						break
					
			for n, t in fields:
				v = None
				nodename = expect in (Event, ) and n or self.__qn(n)
				if issubclass(t.__class__, type):
					if n in ("nic", "disk"):
						v = [ self._broker._get_entity(self.__parse_node(childnode, t, i, experiment)) for i, childnode in enumerate(node.findall(self.__qn(n))) ]
					elif issubclass(t, BasicBrokerEntity):
						childnode = node.find(nodename)
						if childnode is not None:
							v = self.__parse_node(childnode, t, 0, experiment)
							v = self._broker._get_entity(v)
					elif issubclass(t, DynamicReference):
						childnode = node.find(nodename)
						if childnode is not None:
							href = childnode.get("href")
							name = childnode.get("name")
							v = (name or href) and DynamicReference(name = name, href = href) or None
					else:
						if not issubclass(t, (basestring, int, float)):
							raise IllegalFieldType(t)
						v = node.findtext(nodename)
						if v is None:
							if expect.__name__ in ("GroupInfo", "ResourceLocationInfo", "UsageInfo"):
								# FIXED: required for fields in groupInfo and usageInfo
#								print str(node.find(n).text)
								v = node.find(n).text
							elif n == "cpu":
								v = node.findtext(self.__qn("vcpu"))
							elif n == "memory":
								v = node.findtext(self.__qn("vmem"))
							elif n == "instance_type":
								v = node.findtext(self.__qn("type"))
							else:
								v = node.get(n)
						if v is not None:
							if issubclass(t, bool):
								v = v.lower() not in ("f", "false", "", "no", "n")  
							else:
								try:
									v = t(v)
								except (TypeError, ValueError):
									if v:
										raise Surprised("Illegal value for %s ('%s'). Need %s" % (n, v, t), node)
									v = None
				else:
					if not isinstance(t, (list, tuple, set, frozenset)):
						raise IllegalFieldType(t)
					if n in ("interface", "endpoint", "network_link"):
						childnodes = node.findall(nodename)
						v = [ self._broker._get_entity(self.__parse_node(childnode, t[0], i, experiment)) for i, childnode in enumerate(childnodes) ]
					elif n in ( "resourceLocationInfo", ):
						# as with GroupInfo, ResourceLocationInfo works differently
						childnodes = node.findall(n)
						v = [ self._broker._get_entity(self.__parse_node(childnode, t[0], i, experiment)) for i, childnode in enumerate(childnodes) ]
					else:
						childnode = node.find(nodename)
						if childnode is not None:
							subexpect = t and t[0] or str
							if not isinstance(subexpect, type) or not issubclass(subexpect, BasicBrokerEntity):
								raise NotImplementedError()
							v = self.__parse_inner_collection(childnode, subexpect, (experiment is None and issubclass(expect, Experiment)) and href or experiment)
						else:
							#logger.warn( "Failed to parse attribute %s of type %s. '%s' node not found in document %s." %(str(n), str(t), nodename, tostring(node)))
							v = t.__class__()
				values[n] = v
		else:
			values = None

		return EntityData(name = name, location = location, values = values, xml = tostring(node, pretty_print = True), experiment = experiment, href = href, entity_class = expect)
			
	def __parse_inner_collection(self, node, expect, experiment):
		collection = []
		for i, n in enumerate(node, 1):
			real_expect = expect
			if expect is PhysicalRouter and n.tag != self.__qn("physical_router"):
				continue
			if expect == NetworkResource:
				href = n.get("href", "")
				if "be-ibbt" in href:
					real_expect = VirtualWallNetworkResource
				elif "federica" in href:
					real_expect = FedericaNetwork
				else:
					real_expect = DefaultNetworkResource# required so that DefaultNetworkResources will be created
			collection.append(self._broker._get_entity(self.__parse_node_checked(n, real_expect, i, experiment)))
		return collection
	
	@classmethod
	def toprettyxml(klass, entity, fields = None, encoding = "utf-8"):
		name = entity.__class__.__name__.lower()
		if name in ("virtualwallnetworkresource", "defaultnetworkresource", "federicanetwork"):
			name = "network"
		elif name == "sitelink":
			name = "site_link"
		elif name == "groupinfo":
			# GroupInfo -> groupInfo
			name = "groupInfo"
		elif name.endswith("resource"):
			name = name[:-len("resource")]
		
		if name == "groupInfo":
			# FIXED: OpenAccess DB does not like the name space attribute
			# TODO: this may not needed anymore
			root = Element(name)
		else:
			root = Element(name, {"xmlns": klass.XMLNS})
		
		klass.__dump_entity(entity, root, fields = fields)
		
		return tostring(root, pretty_print = True)

	@classmethod
	def __qn(klass, tag):
		return str(QName(klass.XMLNS, tag))
	
	@classmethod
	def __dump_element(klass, parent, fieldname, val, innerdump, entity):
		child = SubElement(parent, fieldname)
		if isinstance(val, BasicBrokerEntity):
		#if innerdump and hasattr(val, "location"):
		#   child.set("href", isinstance(val.location, basestring) and val.location or val.location.url)
			if innerdump and hasattr(val, "url"):
				child.set("href", val.url)
			else:
				klass.__dump_entity(val, child, True)
		elif isinstance(val, DynamicReference):
			child.set(*val.get())
			if val.groups:
				SubElement(child, "groups").text = val.groups
		elif isinstance(val, bool):
			child.text = val and "YES" or "NO"
			if entity.__class__.__name__ == "GroupInfo":
				child.text = val and "true" or "false"
		else:
			if innerdump and isinstance(val, basestring):
				t = entity.get_field_type(fieldname)
				if isinstance(t, type) and issubclass(t, BrokerEntity):
					child.set("href", val)
					return child
			elif isinstance(val, float) and val - int(val) == 0.0:
				val = int(val)
			elif fieldname is "resourceLocationInfo":
				# another corner case for open access DB XML
				klass.__dump_entity(val, child, False)
				return child
			
			if isinstance(val, str):
				val = val.decode("utf-8")
			elif not isinstance(val, basestring):
				val = unicode(val)
			child.text = val
		return child

	@classmethod
	def __dump_entity(klass, entity, node, innerdump = False, fields = None):
		if fields is None:
			_fields = [ name for name, _ in entity.get_fields() ]
			if "name" not in _fields and hasattr(entity, "name"):
				_fields = [ "name" ] + _fields
		else:
			_fields = fields
		
		if isinstance(entity, Disk) and entity.id is not None:
			node.set("id", str(entity.id))
		
		for f in _fields :
			if f in entity.__ignore__:
				continue
			
			val = getattr(entity, f)
			if val or val in (False, 0, 0.0) or (fields is not None and f in fields):
				if isinstance(val, (tuple, list, set, frozenset)):
					if isinstance( fields, dict):
						# to save a specific element of a list,
						# we use a dict to convey the index
						# for example save_as disk
						klass.__dump_element(node, f, val[fields[f]], innerdump, entity)
					elif fields and val:
						klass.__dump_element(node, f, val[0], innerdump, entity)
					else:
						for v in val:
							klass.__dump_element(node, f, v, innerdump, entity)
				else:
					if f == "href":
						node.set("href", getattr(val, "id", str(val)))
					else:
						klass.__dump_element(node, f, val, innerdump, entity) 
					
		if hasattr(entity, "context") and entity.context:
			child = SubElement(node, "context")
			for k, v in entity.context.iteritems():
				SubElement(child, k).text = str(v)
				
		if getattr(entity, "location", None) and not isinstance(entity, AutobahnEndpoint) and not entity.__class__.__name__ == "ResourceLocationInfo":
			SubElement(node, "link", rel = "location", href = getattr(entity.location, "url", entity.location))
	
toprettyxml = OCCISerializer.toprettyxml
