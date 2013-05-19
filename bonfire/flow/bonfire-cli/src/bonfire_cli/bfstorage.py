from bonfire_cli import Formatter, Field
from ResourceTool import ResourceTool
from argparser_types import location_id, experiment_id, boolean_choices, parse_bool
from bonfire.broker import StorageResource
from bonfire.broker.occi import toprettyxml
from exc import ConfigurationError

class StorageFormatter(Formatter):
	__fields__ = [
			Field("description"),
			Field("size", suffix = "MiB"),
			Field("type"),
			Field("fstype", "Filesystem"),
			Field("state"),
			Field("public"),
			Field("persistent")
	]

class BFStorageTool(ResourceTool):
	_entity_type = "storage" 
	
	def _get_arg_parser(self, action, parser):
		super(BFStorageTool, self)._get_arg_parser(action, parser)
		
		if action == "create":
			parser.add_argument("location", type = location_id, help = "BonFIRE site at which this resource will be created")
			parser.add_argument("experiment", type = experiment_id, help = "The Experiment this resource will be part of", nargs = "?")

			parser.add_argument("-D", "--description", default = "<no description>")
			parser.add_argument("-S", "--size", type = int, default = 1024, help = "size in MByte")		
			parser.add_argument("-T", "--type", choices = ("datablock", "shared"), default = "datablock", help = "Storage type")
			parser.add_argument("-F", "--fstype", default = "ext3", help = "Filesystem type")
			parser.add_argument("-P", "--public", action = "store_true", help = "Indicates that this resource should be publicly visible")
			parser.add_argument("-R", "--persistent", action = "store_true", help = "Indicates that this resource should be persistent")
		elif action == "update":
			parser.add_argument("-P", "--public", choices = boolean_choices, help = "Indicates that this resource should be publicly visible")
			parser.add_argument("-R", "--persistent", choices = boolean_choices, help = "Indicates that this resource should be persistent")

		
	def _action_create(self, args):
		newres = StorageResource(args.name, args.location, args.experiment )
		
		if args.group:
			newres.groups = ','.join(args.group)
		newres.description = args.description
		newres.type = args.type.upper()
		newres.size = args.size
		newres.fstype = "ext3"
		newres.persistent = args.persistent
		newres.public = args.public
		
		xml = toprettyxml(newres)
		
		return (args.experiment and (args.experiment + "/storages") or (args.location + "/storages"), xml)
	
	def _action_update(self, args):
		id = self._guess_id(args)
		
		if args.public is None and args.persistent is None:
			raise ConfigurationError("No parameter to update given")
		
		if args.public is not None and args.persistent is not None:
			raise ConfigurationError("Only one parameter can be updated at a time")
		
		r = StorageResource("dummy", None)
		
		if args.public is not None:
			r.public = parse_bool(args.public)
			field = "public"
		elif args.persistent is not None:
			r.persistent = parse_bool(args.persistent)
			field = "persistent"
		
		return (id, toprettyxml(r, (field, )))
	
	def _get_formatter(self, entity, args):
		return StorageFormatter()
