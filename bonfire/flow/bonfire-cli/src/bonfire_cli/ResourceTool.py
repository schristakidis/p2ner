from . import CLITool
from exc import ConfigurationError, CLIError
from actions import ResourceIDAction, ExperimentIDAction, LocationIDAction

class ResourceTool(CLITool):
	_default_location = None
	
	def _get_arg_parser(self, action, parser):
		if action in ("show", "update", "delete", "ssh"):
			parser.add_argument("id", action = ResourceIDAction, help = "Resource ID or name")
			#parser.add_argument("-E", "--experiment", action = ExperimentIDAction, help = "Experiment to search")
			parser.add_argument("-L", "--location", action = LocationIDAction, default = self._default_location, help = "Location to search")
		elif action == "list":
			parser.add_argument("-E", "--experiment", action = ExperimentIDAction, help = "Experiment to search")
			parser.add_argument("-L", "--location", action = LocationIDAction, help = "Location to search")
			
	def _guess_id(self, args):
		return self._do_guess_id(args.id, args.location, self._entity_type)
		
	def _do_guess_id(self, id, location, entity_type):
		if not id.startswith("/"):
			self.logger.debug("not a complete ID ('%s')" % (id, ))
			
			if not location:
				raise ConfigurationError("Need either a complete ID (instead of '%s') or a location (-L)." % (id, ))
			
			try:
				int(id)
			except (ValueError, TypeError):
				self.logger.debug("ID is not numeric. Assuming its a name.")
				for r in getattr(self.broker, "get_" + entity_type + "s")(location):
					if r.name == id:
						id = r.id
						break
				else:
					raise CLIError("Resource not found at %s: %s" % (location, id, ))
			else:
				self.logger.debug("Numeric ID found.")
				id = location + "/" + (entity_type == "federicanetwork" and "network" or entity_type) + "s/" + id
					
			self.logger.debug("Assuming ID is %s" % (id, ))
		
		return id
	
	def _action_show(self, args):
		id = self._guess_id(args)
		return self.broker.get_entity(self._entity_type, id)
	
	def _list_global_resources(self, location):
		f = getattr(self.broker, "get_" + self._entity_type + "s")
		return f(location = location)
	
	def _list_experiment_resources(self, experiment):
		return getattr(experiment, self._entity_type + "s")

	def _action_list(self, args):
		if args.experiment:
			experiment = self.broker.get_experiment(args.experiment)
			resources = self._list_experiment_resources(experiment)
			if args.location:
				resources = [ resource for resource in resources if str(resource.location) == args.location ]
		else:
			resources = self._list_global_resources(args.location)
			
		return resources
	
	def _action_delete(self, args):
		return self._guess_id(args)
	