'''
Created on 28.11.2010

@author: kca
'''

from bonfire.broker import logger
from bonfire.broker.EntityData import EntityData
from xml.dom.minidom import Element, parse, getDOMImplementation
from bonfire.broker.exc import TotallySurprisedError, IllegalFieldType
from bonfire.broker.BrokerEntity import BasicBrokerEntity, BrokerEntity
from AbstractSerializer import AbstractSerializer

dom = getDOMImplementation()

try:
	from xml.dom.ext import PrettyPrint
except ImportError:
	logger.warn("pyxml module not found. XML output will be ugly.")
	def __get_prettyxml(node):
		return node.toxml()
else:
	from cStringIO import StringIO as cStringIO
	def __get_prettyxml(node):
		tmpStream = cStringIO()
		PrettyPrint(node, stream=tmpStream, encoding="utf-8")
		return tmpStream.getvalue()  

def _get_prettyxml(node, name):
	xml = __get_prettyxml(node)
	return xml.replace("<%s>" % (name, ), '<%s xmlns="http://api.bonfire-project.eu/doc/schemas/occi">' % (name, ))
	
def __dump_entity(entity, node, doc, innerdump = False):
		fields = entity.get_fields()
		if hasattr(entity, "name"):
			fields = [ ("name", str )] + fields
			
		for f, _ in fields :
			if f in entity.__ignore__:
				continue
			
			val = getattr(entity, f)
			if val or val in (False, 0, 0.0):
				child = doc.createElement(f)
				node.appendChild(child)
				if isinstance(val, BasicBrokerEntity):
					if innerdump and hasattr(val, "url"):
						child.setAttribute("href", val.url)
					else:
						__dump_entity(val, child, doc, True)
				else:
					child.appendChild(doc.createTextNode(str(val))) 
					
		if hasattr(entity, "context") and entity.context:
			context = entity.context
			child = doc.createElement("context")
			for k, v in context.iteritems():
				tag = doc.createElement(k)
				tag.appendChild(doc.createTextNode(str(v)))
				child.appendChild(tag)
				
			node.appendChild(child)
			
		if hasattr(entity, "location"):
			child = doc.createElement("link")
			child.setAttribute("rel", "location")
			child.setAttribute("href", isinstance(entity.location, basestring) and entity.location or entity.location.url,)
			node.appendChild(child)

def toprettyxml(entity, encoding = "utf-8"):
	#print("topretty: %s" % (entity, ))
	name = entity.__class__.__name__.lower()
	if name.endswith("resource"):
		name = name[:-len("resource")]
	doc = dom.createDocument("http://api.bonfire-project.eu/doc/schemas/occi", name, None)
	
	try:
		__dump_entity(entity, doc.documentElement, doc)
		
		return _get_prettyxml(doc,  name)
	except:
		logger.exception("Error occured during pretty printing")
		raise
	finally:
		doc.unlink()
		
class TotallySurprisedError(TotallySurprisedError):
	def __init__(self, msg, xml, *args, **kw):
		super(TotallySurprisedError, self).__init__(msg, xml, *args, **kw)
		
		self.msg = msg
		if hasattr(xml, "toprettyxml"):
			xml = xml.toprettyxml()
		self.xml = xml
		
class IllegalValue(TotallySurprisedError, ValueError):
	def __init__(self, name, have, need, xml, *args, **kw):
		super(IllegalValue, self).__init__(msg = "Illegal value for %s ('%s'). Need %s" % (name, have, need), xml = xml, *args, **kw)


class OCCISerializer(AbstractSerializer):
	def __get_text(self, node, tag):
		nodes = node.getElementsByTagName(tag)
		if nodes and nodes[0].childNodes:
			return nodes[0].childNodes[0].data
		return None

	def __parse_node(self, node, expect, i, doc, experiment = None):
			if expect is not None and node.tagName != self._get_tagname(expect):
				raise TotallySurprisedError("Unexpected element in xml: %s" % (node.tagName), doc)
			
			if issubclass(expect, BrokerEntity):
				name = node.getAttribute("name")
				href = node.getAttribute("href")
				
				if not name:
					name = self.__get_text(node, "name")
					if not name:
						raise TotallySurprisedError("name missing", node) 	
				
				name = name.strip(" \n\t")
			
				if not href:
					raise TotallySurprisedError("href missing", node)
				
				location = '/'.join(href.split("/", 3)[:3])
				#logger.debug("found location: %s" % (location, ))
			else:
				name = href = location = None
			
			if expect is not None and node.childNodes:
				fields = expect.get_fields()
				values = {}
				
				for n, t in fields:
					if issubclass(t.__class__, type):
						if not issubclass(t, (BasicBrokerEntity, basestring, int)):
							raise IllegalFieldType(t)
						if issubclass(t, BasicBrokerEntity):
							childnodes = node.getElementsByTagName(n)
							if childnodes:
								v = self.__parse_node(childnodes[-1], t, 0, doc, experiment)
								v = self._broker._get_entity(t, v)
							else:
								v = None
						else:
							v = self.__get_text(node, n)
							if v is not None:
								try:
									v = t(v)
								except (TypeError, ValueError):
									raise IllegalValue(n, v, t, node)		
					else:
						if not isinstance(t, (list, tuple, set, frozenset)):
							raise IllegalFieldType(t)
						childnodes = node.getElementsByTagName(n)
						if childnodes:
							subexpect = t and t[0] or str
							if not isinstance(subexpect, type) or not issubclass(subexpect, BasicBrokerEntity):
								raise NotImplementedError()
							v = self.__parse_inner_collection(childnodes[-1], subexpect, doc, experiment)
						else:
							v = None
					values[n] = v
			else:
				values = None
			
			#logger.debug("using location: %s" % ( location, ))
			#print("making data: %s " % (values, ))		
			return EntityData(name = name, location = location, values = values, xml = _get_prettyxml(node, name), experiment = experiment, href = href)
			#return self._broker._get_entity(expect, name, href, experiment, d)
			
	def parse_item_raw(self, xml, expect = None, experiment = None):
		doc = parse(xml)
		try:
			if not doc.childNodes:
				raise TotallySurprisedError(msg = "Document has no root node", xml = doc)
			
			return self.__parse_node(doc.childNodes[0], expect, 1, doc, experiment)
		finally:
			doc.unlink()
		
	def __parse_inner_collection(self, node, expect, doc, experiment):
		i = 0
		items = []
		for node in node.childNodes:
			if isinstance(node, Element):
				i += 1
				e = self.__parse_node(node, expect, i, doc, experiment)
				e = self._broker._get_entity(expect, e)
				items.append(e)
		return items
		
	def parse_collection(self, xml, expect = None, experiment = None):
		doc = parse(xml)
	#	print("got doc")
		try:
			if not doc.childNodes:
				raise TotallySurprisedError(msg = "Document has no root node", xml = doc)
			root = doc.childNodes[0].getElementsByTagName("items")
		
			if not root:
				raise TotallySurprisedError(msg = "Document has no \"items\" node", xml = doc)
			root = root[0]
			
			return self.__parse_inner_collection(root, expect, doc, experiment)
		finally:
			doc.unlink()
			
	def parse_response(self, response):
		if response:
			doc = parse(response)
			try:
				if doc.firstChild:
					return doc.firstChild.getAttribute("href")
			finally:
				doc.unlink()
