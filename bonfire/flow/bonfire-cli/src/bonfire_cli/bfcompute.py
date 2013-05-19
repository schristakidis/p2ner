from bonfire_cli.ResourceTool import ResourceTool
from argparser_types import context_item, location_id, experiment_id, resource_id, int_gtz, float_gtz
from exc import ConfigurationError
from bonfire.broker import ComputeResource, Disk, Nic, DynamicReference
from bonfire.broker.occi import toprettyxml
from string import ascii_lowercase
from util import is_vw, is_cells
from bonfire_cli import Formatter, Field
from logging import DEBUG
from bonfire.exc import BonfireError
from bonfire_cli.exc import CLIError
import sys, os
from bonfire.util import test_port

class ComputeFormatter(Formatter):
	__fields__ = [
			Field("state"),
			Field("host"),
			Field("instance_type", label = "Instance Type"),
			Field("cpu"),
			Field("memory", suffix = "MiB"),
			Field("disk"),
			Field("nic")
	]
	
	def _format_value(self, name, label, value, suffix=u"", index = None):
		if name == "nic" and value:
			result = (self._format_value("nic.ip", label + " IP", value.ip) + 
				self._format_value("nic.mac", label + " MAC", value.mac))
			
			if value.network:
				result.append( (label + " Network", u"%s (%s)" % (self._format_simple(value.network.name), value.network.id)))
			else:
				result.append((label + " Network", "<n/a>"))
			return result
		elif name == "disk":
			if index == 0:
				label = "OS Image"
			return [ (label, u"%s (%s)" % (self._format_simple(value.storage.name), value.storage.id)) ]
		return super(ComputeFormatter, self)._format_value(name, label, value, suffix)
	
	def format_list_details(self, r):
		result = super(ComputeFormatter, self).format_list_details(r)
		result, nicdata = result[:len(self._labels) + 2], result[len(self._labels) + 2:]
		nicstrs = []
		
		while nicdata:
			nic, nicdata = nicdata[:3], nicdata[3:]
			
			if len(nic) != 3:
				continue
			
			nicstrs.append(', '.join(map(': '.join, nic)))
		
		result.append(("NICs", '; '.join(nicstrs)))
		
		return result

class BFComputeTool(ResourceTool):
	_entity_type = "compute"
	
	available_actions = ("show", "list", "create", "update", "delete", "ssh")
	
	def _get_arg_parser(self, action, parser):
		super(BFComputeTool, self)._get_arg_parser(action, parser)
		
		if action == "create":
			parser.add_argument("os_image", type = resource_id, help = "OS image this compute will be based on" )
			parser.add_argument("experiment", type = experiment_id, help = "The Experiment this resource will be part of")
			parser.add_argument("-I", "--instance_type", default = "small", help = "Instance type")
			parser.add_argument("-P", "--cpu", type = float_gtz, default = 1, help = "Only applicable with 'custom' instance type")
			parser.add_argument("-V", "--vcpu", type = int_gtz, default = 1.0, help = "Only applicable with 'custom' instance type")
			parser.add_argument("-M", "--memory", type = int_gtz, default = 512, help = "Only applicable with 'custom' instance type")
			parser.add_argument("-S", "--storage", dest = "storages", action = "append", type = resource_id, help = "Additional Storage Resources to attach")
			parser.add_argument("-N", "--network", dest = "networks", action = "append", type = resource_id, help = "Network Resources to attach")
			parser.add_argument("-L", "--location", type = location_id, help = "Location where this compute will be created")
			parser.add_argument("-C", "--context", action = "append", type = context_item, help = "Context item in the form <key>:<value>")
			parser.add_argument("-R", "--cluster", help = "Cluster to deploy this compute on")
			parser.add_argument("-H", "--host", help = "Host to deploy this compute on")
			parser.add_argument("-X", "--count", type = int_gtz, help = "How many compute resources to create. When set, name mangling will be performed: If the string '%%s' is found in the specified name, it will for each compute created replaced by the computes index. Otherwise, '-<index>' will be appended to the name.")
			parser.add_argument("-k", "--keep-going", action = 'store_true', help = "Keep going in face of errors when --count is given.")
		elif action == "update":
			parser.add_argument("-S", "--state", choices = ("resume", "suspended", "shutdown", "stopped", "cancel"))

			parser.add_argument("-A", "--save-as", help = "Set save-as target")
			parser.add_argument("-G", "--group", help = "The group that will own the OS image resulting from --save-as.")
							
	def _action_create(self, args):
		location = args.location
		
		storages = args.storages or []
		networks = args.networks or []
		
		if not location:
			for rid in [ args.os_image ] + storages + networks:
				if rid.startswith("/locations/"):
					parts = rid.split("/")
					if not parts[3]:
						raise ConfigurationError("Invalid resource ID: %s" % (rid, ))
					location = "/".join(parts[:3])
					break
			else:
				raise ConfigurationError("Unable to derive target location from involved resources. Please specify location through -L.")
			
		os_image = self._do_guess_id(args.os_image, location, "storage")
		storages = [ self._do_guess_id(id, location, "storage") for id in storages ]
		networks = [ self._do_guess_id(id, location, "network") for id in networks ]
		vw = is_vw(location)
			
		newres = ComputeResource(name = args.name, location = location, experiment = args.experiment)
		
		newres.instance_type = args.instance_type
		if args.instance_type == "custom":
			newres.cpu = args.cpu
			newres.vcpu = args.vcpu
			newres.memory = args.memory
			
		newres.disk = [ Disk(os_image) ]
		newres.disk[0].type = "OS"
		if not vw:
			newres.disk[0].target = "hda"
			
		drive_letters = ascii_lowercase[1:]
				
		for storage, drive_letter in zip(storages, drive_letters):
			disk = Disk(storage)
			disk.type = "DATABLOCK"
			if not vw:
				disk.target = "hd" + drive_letter
			newres.disk.append(storage)
		
		if not networks:
			#TODO: Make this configurable
			if is_cells(location):
				networks = (self._do_guess_id("Internet@HP", location, "network"), )
			else:
				networks = (self._do_guess_id("BonFIRE WAN", location, "network"), )
			
		newres.nic = map(Nic, networks)
		
		if args.context:
			contextvars = []
			for k, v in args.context:
				if k in contextvars:
					raise ConfigurationError("Duplicate context variable: %s" % (k, ))
				contextvars.append(k)
				newres.set_context(k, v)
				
		newres.cluster = args.cluster
		newres.host = args.host
			
		if not args.count:
			xml = toprettyxml(newres)
		else:
			nametemplate = args.name
			if "%s" not in nametemplate:
				nametemplate += "-%s"
			
			xml = [  ]
			for i in range(args.count):
				newres.name = nametemplate.replace("%s", str(i + 1))
				xml.append( toprettyxml(newres) )
		
		return (args.experiment + "/computes", xml)
	
	def _action_update(self, args):
		id = self._guess_id(args)
		
		if args.save_as is None and args.state is None:
			raise ConfigurationError("No parameter to update given")
		
		if args.save_as is not None and args.state is not None:
			raise ConfigurationError("Only one parameter can be updated at a time")
		
		if args.state is not None and args.group is not None:
			raise ConfigurationError("--group is online applicable in connection with --save-as.")
		
		r = ComputeResource("dummy", None)
		
		if args.state is not None:
			r.state = args.state
			field = "state"
		elif args.save_as is not None:
			r.disk = [ Disk() ]
			r.disk[0].save_as = DynamicReference(name = args.save_as, groups = args.group)
			field = "disk"
		
		return (id, toprettyxml(r, (field, )))
	
	_action_ssh = ResourceTool._action_show
	
	def _parse_action_args(self, args, parser):
		target = cliargs = []
		sshargs = []
		found_delimiter = False
		
		for a in args:
			if not found_delimiter and a == "--":
				found_delimiter = True
				target = sshargs
			else:
				target.append(a)
			
		args = super(BFComputeTool, self)._parse_action_args(cliargs, parser)
		
		args.sshargs = sshargs
		
		return args
	
	def _handle_result(self, action, args, result):
		if action == "ssh":
			ip = result.wan_nic.ip
			if not ip:
				raise CLIError("WAN nic of %s has no IP assigned." % (result.id, ))
			
			testresult = test_port(ip, 22, timeout = 5)
			if testresult:
				self.logger.debug("Seems like we do not need to use an SSH gateway.")
				ssh_cmd = [ "ssh", "root@%s" % (ip, ) ] + args.sshargs
			else:
				self.logger.info("Direct connection attempt failed: %s" % (testresult.message, ))
				
				ssh_gateway = "ssh.fr-inria.bonfire-project.eu"
				
				self.logger.info("Using SSH gateway %s" % (ssh_gateway, ))
				
				ssh_options_str = ' '.join(args.sshargs)
				username = self._get_brokerargs().get("username")
				
				ssh_cmd = [
						"ssh", "-o", 
						"ProxyCommand=ssh %s %s%s \"nc -w 60 %%h %%p\"" % (ssh_options_str, username and username + "@" or "", ssh_gateway),
						 "-o", "StrictHostKeyChecking=no", 
						 "root@%s" % (ip, )
				] + args.sshargs
			
			self.logger.info("Attempting to connect to %s" % (ip, ))
			self.logger.debug("Executing: %s" % (ssh_cmd, ))
			
			self.out.flush()
			sys.stderr.flush()
			
			os.execvp("ssh", ssh_cmd)
		else:
			super(BFComputeTool, self)._handle_result(args, result)	
	
	def _get_formatter(self, entity, args):
		return ComputeFormatter()
	
	def _request(self, method, uri, data, args):
		if not isinstance(data, (tuple, list, set)):
			super(ResourceTool, self)._request( method, uri, data, args)
		else:
			for d in data:
				try:
					super(ResourceTool, self)._request( method, uri, d, args)
				except BonfireError, e:
					if not args.keep_going:
						raise
					if self.logger.isEnabledFor(DEBUG):
						self.logger.exception("Request failed: %s %s", method, uri)
					else:
						self.logger.error(e)
