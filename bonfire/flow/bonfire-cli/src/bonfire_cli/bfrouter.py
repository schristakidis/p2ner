from bonfire_cli import Formatter, Field 
from ResourceTool import ResourceTool
from argparser_types import location_id, experiment_id, interface
from bonfire.broker.federica import Router
from bonfire.broker.occi import toprettyxml

class RouterFormatter(Formatter):
	__fields__ = [
		Field("host"),
		Field("status"),
		Field("interfaces", "Interface"),
		Field("config"),
	]
	
	# return a list of interfaces
	def get_interfaces(self, o):
		return [ 'Name="%s" IP="%s" Netmask="%s" PhysicalInterface="%s"' % (r.name, r.ip, r.netmask, r.physical_interface) for r in o.interface ]

class BFRouterTool(ResourceTool):
	_entity_type = "router"
	_default_location = "/locations/federica"
	_iface_spec = '"<name>,<physical if>[,<ip>[,<netmask>]]"'
	
	def _get_arg_parser(self, action, parser):
		super(BFRouterTool, self)._get_arg_parser(action, parser)
		
		if action == "create":
			parser.add_argument("host", type = str, help = "Physical router to host this resource")
			parser.add_argument("location", type = location_id, help = "BonFIRE site at which this resource will be created")
			parser.add_argument("experiment", type = experiment_id, help = "The Experiment this resource will be part of")
			parser.add_argument("interface", type = interface, nargs = "+", help = "Interface description: " + self._iface_spec)
			parser.add_argument("-C", "--config", type = str, default = "", help = "Router configuration")

	def _action_create(self, args):
		newres = Router(args.name, args.location, args.experiment)

		if args.group:
			newres.groups = ','.join(args.group)
		newres.host = args.host
		for interface in args.interface:
			newres.interface.append(interface)
		newres.config = args.config

		xml = toprettyxml(newres)
		
		return (args.experiment + "/routers", xml)
	
	def _get_formatter(self, entity, args):
		return RouterFormatter()
	