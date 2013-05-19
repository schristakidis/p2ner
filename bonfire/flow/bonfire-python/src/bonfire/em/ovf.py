from bonfire.em.exc import EMError
from bonfire.em.ManagedExperiment import ManagedExperiment
from . import logger 

try:
	from lxml.etree import ElementTree, XMLSyntaxError as ParseError, tostring as _ts
	def tostring(element, pretty_print = False):
		return _ts(element, encoding = "utf-8", pretty_print = pretty_print)
except ImportError:
	from xml.etree.ElementTree import ElementTree, ParseError, tostring as _ts
	def tostring(element, pretty_print = False):
		return _ts(element, encoding = "utf-8")

class EDError(EMError):
	pass

class EDParser(object):
	def __init__(self, em):
		self.em = em
	
	def __parse(self, buffer):
		try:
			return ElementTree().parse(buffer)
		except ParseError, e:
			raise EDError(e)
		
	def parse(self, buffer):
		return self._parse_item(self.__parse(buffer))
	
	def parse_collection(self, buffer):
		doc = self.__parse(buffer)
		
		if doc.tag != "collection" or not len(doc) or doc[0].tag != "items":
			raise EDError("Input does not seem to be a list of managed experiments")
		
		result = []
		for elem in doc[0]:
			try:
				result.append(self._parse_item(elem))
			except EDError, e:
				logger.exception("Error parsing managed experiment in collection: %s (%s)" % (e, tostring(elem)))
		return result
		
	def _parse_item(self, doc):	
		if doc.tag != "managed_experiment":
			raise EDError("Wrong tagname (%s) on item. Must be managed_experiment. (%s)" % (doc.tag, tostring(doc)))
		href = doc.get("href")
		name = doc.findtext("name")
		if not href:
			raise EDError("href missing in ED (%s)" % (tostring(doc, )))
		if name is None:
			raise EDError("name missing in ED (%s)" % (tostring(doc, )))
		status = doc.findtext("status", "")
		description = doc.findtext("description", "")
		experiment_url = log_url = None
		for l in doc.findall("link"):
			rel = l.get("rel")
			if rel == "log":
				log_url = l.get("href")
			elif rel == "experiment":
				experiment_url = l.get("href")
		return ManagedExperiment(href, name, description, status, log_url, experiment_url, tostring(doc, True), self.em)
	
	