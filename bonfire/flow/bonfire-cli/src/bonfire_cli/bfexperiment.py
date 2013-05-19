import iso8601
from datetime import timedelta

from bonfire_cli import CLITool, Formatter, Field
from bonfire.broker import Experiment
from bonfire.broker.occi import toprettyxml

from argparser_types import experiment_id, duration
from exc import ConfigurationError

class ExperimentFormatter(Formatter):
	__fields__ = [
		Field("description"),
		Field("status"),
		Field("walltime"),
		Field("created_at", "Created"),
		Field("updated_at", "Updated"),
		Field("expires_at", "Expires"),
		Field("aggregator_password", "Aggregator Password")
	]
	
	def get_walltime(self, r):
		if r.walltime is None:
			return None
		
		days, secs = divmod(r.walltime, 24 * 60 * 60)
		hours, secs = divmod(secs, 60 * 60)
		mins, secs = divmod(secs, 60)
		
		vals = []
		if days:
			vals.append("%sd" % (days, )) 
		if hours:
			vals.append("%sh" % (hours, ))
		if mins:
			vals.append("%sm" % (mins, ))
		if secs:
			vals.append("%ss" % (secs, ))
			
		return "%ss (%s)" % (r.walltime, ''.join(vals))
	
	def get_expires_at(self, r):
		if r.created_at and r.walltime:
			return (iso8601.parse_date(r.created_at) + timedelta(seconds = r.walltime)).strftime("%Y-%m-%dT%H:%M:%SZ")
		raise ValueError("cannot calculate expiration date: created_at=%s, walltime=%s" % (r.created_at, r.walltime))

class BFExperimentTool(CLITool):
	def _get_arg_parser(self, action, parser):
		if action in ("show", "update", "delete"):
			parser.add_argument("id", type = experiment_id, help = "Experiment ID")
			
		if action == "create":
			parser.add_argument("-D", "--description", default = "<no description>")
			parser.add_argument("-W", "--walltime", type = duration, default = 24 * 60 * 60, help = "Lifetime of the experiment either in seconds or as a string like '3days10h5mi30s' are possible.")
			parser.add_argument("-A", "--aws-access-key-id", help="AWS access key ID. Requires --aws_secret_access_key as well.")
			parser.add_argument("-K", "--aws_secret_access_key", help="AWS secret key. Requires --aws-access-key-id as well.")
		elif action == "update":
			parser.add_argument("-S", "--status", choices = ("running", "stopped"))
		
	def _action_create(self, args):
		newres = Experiment(args.name)
		
		if args.aws_access_key_id or args.aws_secret_access_key:
			if not args.aws_access_key_id:
				raise ConfigurationError("--aws_access_key_id required for AWS enabled experiments.")
			if not args.aws_secret_access_key:
				raise ConfigurationError("--aws_secret_access_key required for AWS enabled experiments.")
			newres.aws_access_key_id = args.aws_access_key_id
			newres.aws_secret_access_key = args.aws_secret_access_key
		
		if args.group:
			newres.groups = ','.join(args.group)
		newres.description = args.description
		newres.walltime = args.walltime

		xml = toprettyxml(newres)
		
		return ("/experiments", xml)
	
	def _action_show(self, args):
		return self.broker.get_experiment(args.id)
	
	def _action_list(self, args):
		return self.broker.get_experiments()
	
	def _action_update(self, args):
		if args.status is None:
			raise ConfigurationError("No parameter to update given")
		
		e = Experiment("dummy")
		e.status = args.status
		return (args.id, toprettyxml(e, ("status",)))
	
	def _action_delete(self, args):
		return args.id
	
	def _get_formatter(self, entity, args):
		return ExperimentFormatter()
