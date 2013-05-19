from bonfire_cli import Formatter, Field
from ResourceTool import ResourceTool
from argparser_types import location_id, experiment_id, bandwidth
from bonfire.broker.Sitelink import Sitelink, AutobahnEndpoint
from bonfire.broker.occi import toprettyxml

class SitelinkFormatter(Formatter):
	__fields__ = [
			Field("description"),
			Field("endpoint_1", label = "Endpoint 1"),
			Field("endpoint_2", label = "Endpoint 2"),
			Field("bandwidth", suffix = "MB"),
			Field("status")
	]
	
	def get_endpoint_1(self, r):
		return self._get_endpoint(r, 0)
		
	def get_endpoint_2(self, r):
		return self._get_endpoint(r, 1)
		
	def _get_endpoint(self, r, i):
		try:
			e = r.endpoint[i]
			return "%s (VLAN %s)" % (e.href, e.vlan)
		except:
			return "<n/a>"

class BFSitelinkTool(ResourceTool):
	_entity_type = "sitelink" 
	_default_location = "/locations/autobahn"
	
	available_actions = ("show", "list", "create", "delete")
	
	def _get_arg_parser(self, action, parser):
		super(BFSitelinkTool, self)._get_arg_parser(action, parser)
		
		if action == "create":
			parser.add_argument("location", type = location_id, help = "BonFIRE site at which this resource will be created")
			parser.add_argument("experiment", type = experiment_id, help = "The Experiment this resource will be part of")

			parser.add_argument("-D", "--description", default = "<no description>")
			parser.add_argument("-E", "--endpoint", type = location_id, nargs = 2, default = ["/locations/uk-epcc", "/locations/pl-psnc"], help = "Endpoints to connect")
			parser.add_argument("-B", "--bandwidth", type = bandwidth, default = 10, help = "Network bandwidth in Mbps (min: 1Mbps)")

		
	def _action_create(self, args):
		newres = Sitelink(args.name, args.location, args.experiment )
		
		if args.group:
			newres.groups = ','.join(args.group)
		newres.description = args.description
		newres.bandwidth = args.bandwidth
		newres.endpoint = map(AutobahnEndpoint, args.endpoint)
		
		xml = toprettyxml(newres)
		
		return (args.experiment + "/site_links" , xml)
	
	def _get_formatter(self, entity, args):
		return SitelinkFormatter()
