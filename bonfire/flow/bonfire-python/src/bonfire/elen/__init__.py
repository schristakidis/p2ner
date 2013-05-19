import logging 
from exc import ElenError
from xmlrpclib import ServerProxy

class MethodDispatcher(object):
	def __init__(self, method, *args, **kw):
		super(MethodDispatcher, self).__init__(*args, **kw)
		self._method = method
		
	def __call__(self, *args):
		try:
			return self._method(*args)
		except Exception, e:
			raise ElenError("Error calling method", e)
		
	def __getattr__(self, name):
		return self.__class__(getattr(self._method, name))

class ElenServerProxy(ServerProxy):
	method_dispatcher = MethodDispatcher
	
	def __init__(self, uri, transport=None, encoding=None, verbose=0, allow_none=0, use_datetime=0, method_dispatcher = None):
		ServerProxy.__init__(self, uri = uri, transport = transport, encoding = encoding, verbose = verbose, allow_none = allow_none, use_datetime = use_datetime)
		if method_dispatcher:
			self.method_dispatcher = method_dispatcher
			
	def __getattr__(self, name):
		return MethodDispatcher(ServerProxy.__getattr__(self, name))
			
class ElenClient(object):
	logger = logging.getLogger("bonfire.broker")
	
	def __init__(self, uri, *args, **kw):
		super(ElenClient, self).__init__(*args, **kw)
		if "://" not in "uri":
			if ":" not in uri and "/" not in uri:
				uri = uri + ":8090"
			uri = "http://" + uri
		self.uri = uri
		
	def deploy(self, name, os_image, network, instance_type, max = 10, max_cpu = 60, port = None):
		vmgroup = {
			"name": name, 
			"min": "1",
			"max": str(int(max))
		}
		
		service_type = port and {"scheme": "HAProxy", "port": int(port)} or None
		
		triggers = {
				"trigger_1": {
					"name": "upscale",
					"type": "passive",
					"expression": "{system.cpu.load[,avg1].last(0)}>%s" % (int(max_cpu), ),
					"strategy": "de.fhg.fokus.elen.strategies.CPUupscaleTriggersProcessor",
				},
				"trigger_2": {
					"name": "downscale",
					"type": "passive",
					"expression": "{system.cpu.load[,avg1].last(0)}<35",
					"strategy": "de.fhg.fokus.elen.strategies.NewCpuDownscale",
				},
		}
		
		template = { "diskSource": getattr(os_image, "url", os_image) }
		
		if isinstance(instance_type, (tuple, list, set, frozenset)):
			template["cpu"], template["VCpu"], template["memory"] = instance_type
			template["instance_type"] = "custom"
		else:
			template["instance_type"] = instance_type
			
		self.logger.debug("Calling Elasticity Engine at %s with name=%s template=%s triggers=%s service_type=%s" % (self.uri, name, template, triggers, service_type))
		
		result = self._get_elen().eaas.addAndInitGroup(vmgroup, template, service_type, triggers)
		
		return result
	
	def list(self):
		result = self._get_elen().eaas.listRunningVMs()
			
		return result
	
	def get_endpoint(self):
		result = self._get_elen().eaas.getLoadBalancer()

		if not result: 
			return None

		try:
			return "%s:%s" % (result["ip"], result["port"])
		except:
			self.logger.exception("Failed to build endpoint string from %s", result)
			return None
			
	def _get_elen(self):
		return ElenServerProxy(self.uri, allow_none = True)
	