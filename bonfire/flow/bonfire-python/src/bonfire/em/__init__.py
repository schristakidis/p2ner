from bonfire.http.RestClient import RestClient
import logging
from bonfire.broker.occi.AbstractSerializer import etree
from exc import EMError

if etree is not None:
	from cStringIO import StringIO
	from bonfire.broker.occi.AbstractSerializer import XMLSyntaxError, DocumentInvalid

logger = logging.getLogger("bonfire.em")

class ExperimentManager(object):
	asserted_id_header = "X-Bonfire-Asserted-Id"
	
	def __init__(self, uri, certfile = None, keyfile = None, ovf_schema = None, *args, **kw):
		super(ExperimentManager, self).__init__(*args, **kw)
		self.uri = uri
		self.__restclient = RestClient(uri, certfile = certfile, keyfile = keyfile, content_type = "application/json", component_name = "Experiment Manager")
		from bonfire.em.ovf import EDParser
		self.__parser = EDParser(self)
		
		if etree is not None and ovf_schema is not None:
			xmlschema_doc = etree.parse(ovf_schema)
			self.__xmlschema = etree.XMLSchema(xmlschema_doc)
		else:
			self.__xmlschema = None

	def submitJSON(self, json, user, group = None):
		return self._submit("application/json", json, user, group)
	
	def submitOVF(self, ovf, user, group = None):
		return self._submit("application/xml", ovf, user, group)
		
	def _submit(self, content_type, data, user, group):
		headers = {
				self.asserted_id_header: str(user),
				"Content-Type": content_type
		}
		if group:
			headers["X-BONFIRE-ASSERTED-SELECTED-GROUP"] = str(group)
		with self.__restclient.request("POST", "/managed_experiments", data, headers) as xml:
			return self.__parser.parse(xml)
			
	def list(self, user):
		with self.__restclient.get("/managed_experiments", headers = {self.asserted_id_header: str(user)}, args = {"user_id": str(user)}) as xml:
			return self.__parser.parse_collection(xml)
		
	def get(self, id, user):
		if not id:
			raise ValueError(id)
		
		with self.__restclient.get(id, headers = {self.asserted_id_header: str(user)}) as xml:
			return self.__parser.parse(xml)
		
	def delete(self, id, user):
		self.__restclient.delete(id, headers = {self.asserted_id_header: str(user)})
		
	def get_log(self, url, user):
		url = getattr(url, "log_url", url)
		with self.__restclient.get(url, {self.asserted_id_header: str(user)}) as input:
			return input.read()
		
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
				raise EMError("Error validating OVF XML: " + str(e)) 
		