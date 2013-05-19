from bonfire_cli import Field, Formatter
from ResourceTool import ResourceTool
from argparser_types import location_id, experiment_id, ip_address, lossrate, latency, bandwidth, int_gtz, cidr_prefix
from bonfire.broker import VirtualWallNetworkResource, DefaultNetworkResource
from bonfire.broker.occi import toprettyxml
from util import is_cells, is_vw, is_aws, is_autobahn, is_federica
from exc import ConfigurationError

class NetworkFormatter(Formatter):
	__fields__ = [
		Field("address"), 
		Field("size"),
	]
	
class DefaultValue(object):
	pass

class DefaultString(DefaultValue, str):
	pass

class DefaultInt(DefaultValue, int):
	pass

class BFNetworkTool(ResourceTool):
	_entity_type = "network"
	
	def _get_arg_parser(self, action, parser):
		super(BFNetworkTool, self)._get_arg_parser(action, parser)
		
		if action == "create":
			parser.add_argument("location", type = location_id, help = "BonFIRE site at which this resource will be created")
			parser.add_argument("experiment", type = experiment_id, help = "The Experiment this resource will be part of")

			parser.add_argument("-A", "--address", type = ip_address, default = "192.168.0.0", help = "Network address. Applicable to networks on ONE and VW sites.")			
			parser.add_argument("-S", "--size", choices = ("A", "B", "C"), default = DefaultString("C"), help = "Network size specified as network class. Applicable to VW sites.")
			parser.add_argument("-X", "--prefix", type = cidr_prefix, default = DefaultInt(24), help = "Network size specified as CIDR prefix. Applicable to CELLS sites.")
			parser.add_argument("-N", "--netmask", type = ip_address, default = DefaultString("255.255.255.0"), help = "Network size specified as bit mask. Applicable to ONE sites.")
			parser.add_argument("-V", "--vlan", type = int_gtz, help = "VLAN ID")
			parser.add_argument("-P", "--public", action = "store_true", help = "Indicates that this resource should be publicly visible")

			parser.add_argument("-L", "--latency", type = latency, help = "Network latency in ms. (min: 2ms)")			
			parser.add_argument("-R", "--lossrate", type = lossrate, help = "Network lossrate (0.0 - 1.0)")
			parser.add_argument("-B", "--bandwidth", type = bandwidth, help = "Network bandwidth in Mbps (min: 1Mbps)")
			
			parser.add_argument("-C", "--protocol", choices = ("TCP", "UDP"), default = DefaultString("TCP"), help = "Type of generated background traffic. Specifying this implies the creation of an active network and thus requires --packetsize and --throughput as well.")
			parser.add_argument("-K", "--packetsize", type = int_gtz, help = "Packetsize of generated background traffic in bytes. Specifying this implies the creation of an active network and thus requires --protocol and --throughput as well.")
			parser.add_argument("-U", "--throughput", type = int_gtz, help = "Number of generated background traffic packets per second. Specifying this implies the creation of an active network and thus requires --packetsize and --protocol as well.")
			
			parser.add_argument("-T", "--type", choices = ("managed", "active"), help = "Force the type of this network to be either managed or active. If this option is missing the type will be derived from other options.")
					
	def _check_options(self, args, forbidden, tail = None):
		for n in forbidden:
			v = getattr(args, n)
			if v is not None and not isinstance(v, DefaultValue):
				raise ConfigurationError("--%s is not applicable to networks on %s.%s" % (n, args.location, tail and (" " + tail) or ""))
			
	def _action_create(self, args):
		if is_aws(args.location) or is_autobahn(args.location) or is_federica(args.location):
			raise ConfigurationError("Creation of network resources is not supported on %s" % (args.location, ))
		
		if is_vw(args.location):
			newres = VirtualWallNetworkResource(args.name, args.location, args.experiment)
			self._check_options(args, ("netmask", "prefix"), "Consider using --size.")
			
			for n in ("address", "size", "latency", "lossrate", "bandwidth"):
				setattr(newres, n, getattr(args, n))
					
			if args.packetsize or args.throughput or not isinstance(args.protocol, DefaultValue):
				for n in ("packetsize", "throughput", "protocol"):
					v = getattr(args, n)
					if v is None:
						raise ConfigurationError("Active networks require --%s." % (n, ))
					setattr(newres, n, v)
				newres.type = args.type or "active"
			else:
				newres.type = args.type or "managed"
		else:
			newres = DefaultNetworkResource(args.name, args.location, args.experiment )
			if is_cells(args.location):
				self._check_options(args, ("address", "latency", "lossrate", "bandwidth", "protocol", "packetsize", "throughput", "type"), "They only support --prefix.")					
				self._check_options(args, ("netmask", "size"), "Consider using --prefix.")
				newres.size = args.prefix
			else:
				self._check_options(args, ("latency", "lossrate", "bandwidth", "protocol", "packetsize", "throughput", "type"))
				self._check_options(args, ("size", "prefix"), "Consider using --netmask.")					
				
				for n in ("address", "netmask", "vlan"):
					setattr(newres, n, getattr(args, n))
			
		newres.public = args.public			
		if args.group:
			newres.groups = ','.join(args.group)

		xml = toprettyxml(newres)
		
		return (args.experiment + "/networks", xml)
	
	def _list_experiment_resources(self, experiment):
		return experiment.real_networks
	
#	def _get_formatter(self, entity, args):
#		return NetworkFormatter()

	