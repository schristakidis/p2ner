from bonfire_cli import Formatter, Field
from ResourceTool import ResourceTool
from argparser_types import location_id, experiment_id, network_link
from bonfire.broker.federica import FedericaNetwork
from bonfire.broker.occi import toprettyxml

class FedericaNetworkFormatter(Formatter):
	__fields__ = [
			Field("vlan"),
			Field("status")
	]

class BFFedericaNetworkTool(ResourceTool):
	_entity_type = "federicanetwork" 
	_default_location = "/locations/federica"

	available_actions = ("show", "list", "create", "delete")
	
	def _get_arg_parser(self, action, parser):
		super(BFFedericaNetworkTool, self)._get_arg_parser(action, parser)
		
		if action == "create":
			parser.add_argument("location", type = location_id, help = "BonFIRE site at which this resource will be created")
			parser.add_argument("experiment", type = experiment_id, help = "The Experiment this resource will be part of")
			parser.add_argument("network_link", type = network_link, nargs = "+", help = 'A number of network links specified in the form of "<router1>,<interface1>,<router2>,<interface2>"')

	def _action_create(self, args):
		newres = FedericaNetwork(args.name, args.location, args.experiment )
		
		if args.group:
			newres.groups = ','.join(args.group)
			
		newres.network_link = args.network_link
		
		xml = toprettyxml(newres)
		
		return (args.experiment + "/networks" , xml)
	
	def _get_formatter(self, entity, args):
		return FedericaNetworkFormatter()
	
	def _list_experiment_resources(self, experiment):
		return experiment.federica_networks
