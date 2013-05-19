from . import CLITool
from argparser_types import location_id
from bonfire_cli import Formatter, Field

class LocationFormatter(Formatter):	
	__fields__ = [
		Field("type"),
		Field("ssh_gateway", "SSH Gateway"),
		Field("instance_types", "Instance Types")
	]

	def _format_resource(self, r):
		site, self._configurations, self._site_info = r
		return super(LocationFormatter, self)._format_resource(site)
	
	def get_instance_types(self, r):
		if not self._configurations:
			return None
		
		return ', '.join(map(str, self._configurations))

class BFLocationTool(CLITool):
	_entity_type = "location"
	
	available_actions = ("show", "list")

	def _get_arg_parser(self, action, parser):
		if action == "show":
			parser.add_argument("id", type = location_id, help = "Location ID")
			
	def _action_list(self, args):
		return self.broker.get_sites()
	
	def _action_show(self, args):
		site = self.broker.get_site(args.id)
		return self._get_details(site)
	
	def _get_details(self, site):
		return (site, site.supports_type("storage") and site.get_configurations() or (), site.site_info)
	
	def _get_formatter(self, entity, args):
		return LocationFormatter()