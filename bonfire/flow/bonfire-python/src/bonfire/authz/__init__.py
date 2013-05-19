import logging
from bonfire import Entity
from bonfire.http.RestClient import RestClient
from bonfire.broker.occi.etree import OCCISerializer, toprettyxml
from bonfire.http.exc import RemoteError
from exc import AuthZError

class AuthZResult(Entity):
	__fields__ = (
		("suspended", bool),	
		("reason", str),
	)

class ResourceLocationInfo(Entity):
	__fields__ = (
		("location", str),
		("resource", str),
	)
	
	def __init__(self, xml = None, broker = None, fields = False, *args, **kw):
		super(ResourceLocationInfo, self).__init__(fields = fields, *args, **kw)

	def __str__(self):
		return "RLI: %s: %s" %(self.location, self.resource)

class GroupInfo(Entity):
	__fields__ = (
		("id", str),
		("endDate", str),
		("maxComputes", int),
		("maxCpus", float),
		("maxNetworks", int),
		("maxStorage", float),
		("startDate", str),
		("resourceLocationInfo", [ ResourceLocationInfo ]),
		("suspended", bool),
	)
	
	def __init__(self, broker = None, xml = None, fields = False, *args, **kw):
		super(GroupInfo, self).__init__(fields = fields, *args, **kw)
	
class UsageInfo(Entity):
	__fields__ = (
		("computes", int),
		("cpus", float),
		("storage", float)
	)
	
	def __init__(self, xml, broker, fields = False, *args, **kw):
		super(UsageInfo, self).__init__(fields = fields, *args, **kw)
	
	def __str__(self):
		return "UsageInfo: %s %s %s" %(self.computes, self.cpus, self.storage)
	
class AuthZClient(object):
	logger = logging.getLogger("bonfire.authz")
	
	def __init__(self, url, broker, certfile = None, keyfile = None, username = None, password = None, timeout = None, get_timeout = None, *args, **kw):
		super(AuthZClient, self).__init__(*args, **kw)
		self.url = url
		self.__restclient = RestClient(url, certfile = certfile, keyfile = keyfile, 
				timeout = timeout, get_timeout = get_timeout, username = username, password = password,
				component_name = "openaccess db", content_type = "application/xml")
		
		self.__serializer = OCCISerializer(broker = broker)
		
	def get_groupinfo(self, groupid, create_missing = True):
		groupid = str(groupid)
		try:
			xml = self.__restclient.get("/groupinfo/" + groupid)
		except RemoteError, e:
			if not create_missing or e.code != 404:
				raise AuthZError("groupinfo not found for %s" % (groupid, ))
			
			self.logger.info("Group %s is unknown. Creating it." % (groupid, ))
			xml = self.add_groupinfo(groupid)
		
		with xml:
			return self.__serializer.parse_item(xml, GroupInfo)
	
	def add_groupinfo(self, groupid):
		groupinfo = GroupInfo()
		groupinfo.id = groupid
		groupinfo.suspended = False
		xml = toprettyxml(groupinfo)
		data = self.__restclient.post("/groupinfo/", xml)
		return data
			
	
	def put_groupinfo(self, groupinfo):
		"""	Requests a PUT on the open access DB for the supplied groupinfo.
		"""
		xml = toprettyxml(groupinfo)
		#self.logger.debug(xml)
		return self.__restclient.put("/groupinfo/" + groupinfo.id, xml)

	def get_usage(self, groupid):
		"""	Requests a GET for a group's usageInfo from the open access DB
			and returns it as a UsageInfo instance.
		"""
		groupid = str(groupid)
		try:
			xml = self.__restclient.get("/groupinfo/" + groupid + "/usage")
		except RemoteError:
			raise
		
		with xml:
			return self.__serializer.parse_item(xml, UsageInfo)
	