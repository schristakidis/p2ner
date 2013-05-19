import sys, logging, os

# basic logging configuration
#logging.basicConfig( level = logging.WARN, format='[%(name)s] %(levelname)s: %(message)s' )

_logging_formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
_logging_handler = logging.StreamHandler()
_logging_handler.setFormatter(_logging_formatter)
logging.getLogger().addHandler(_logging_handler)

from os.path import expanduser, expandvars, exists
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, SUPPRESS
from collections import namedtuple
from getpass import getpass
from operator import attrgetter, itemgetter
from urllib2 import urlparse
from time import time, sleep

import bonfire
import bonfire.version
import bonfire.broker.occi.etree
from bonfire.util import errorstr
from bonfire.exc import BonfireError
from bonfire.broker import Broker

from exc import ConfigurationError, CLIError
from version import VERSION
from argparser_types import int_gtz, float_gtz, separator

from bonfire.broker import Site

def uc(s):
	if isinstance(s, unicode):
		return s
	if isinstance(s, basestring):
		return s.decode("utf-8")
	return unicode(s)

class Field(namedtuple("FieldBase", ("name", "label", "suffix"))):
	def __new__(cls, name, label = "", suffix = ""):
		return super(Field, cls).__new__(cls, name = name, label = label or name.capitalize(), suffix = suffix)

class Formatter(object):
	__fields__ = []
	
	logger = logging.getLogger("bonfire.cli")
	
	# returns (label, value)
	def _format_field(self, name, label, value, suffix = u""):
		result = []
		if isinstance(value, (tuple, list, set)):
			if value:
				for i, v in enumerate(value):
					l = label + " " + str(i + 1)
					result.extend( self._format_value(name, l, v, suffix, i))					
			else:
				result.append((label, "<none>"))
		else:
			result.extend(self._format_value(name, label, value, suffix)) 
			
		return result
			
	def _format_value(self, name, label, value, suffix = u""):
		return [ (label, self._format_simple(value, suffix)) ]
	
	def _format_simple(self, value, suffix = ""):
		if value or value == 0:
			return uc(value) + uc(suffix)
		return u"<n/a>"
	
	def __call__(self, r):
		return self._format_resource(r)
	format_list_details = __call__
		
	def _format_resource(self, r):
		vals = [ ("Id", r.id), ("Name", r.name) ]
		
		try:
			if not isinstance(r, Site):
				vals.extend( self._format_value("group", "Group", r.group, "") )
		except:
			pass
		
		for name, label, suffix in self.__fields__:
			try:
				# return a custom getter implemented in the Formatter 
				# if available
				getter = getattr(self, "get_" + name)
			except AttributeError:
				getter = attrgetter(name)
				
			try:
				val = getter(r)
			except:
				if self.logger.isEnabledFor(logging.DEBUG):
					self.logger.exception("Failed to get attribute '%s'", name)
				vals.append((label, "<n/a>"))
			else:
				vals.extend( self._format_field(name, label, val, suffix) )
		return vals
		
	@property
	def headers(self):
		return ["Id", "Name"] + self._labels
		
	@property
	def _names(self):
		try:
			return self.__names
		except AttributeError:
			self.__names = names = map(itemgetter(0), self.__fields__)
			return names
		
	@property
	def _labels(self):
		try:
			return self.__labels
		except AttributeError:
			self.__labels = labels = map(itemgetter(1), self.__fields__)
			return labels
		
	@property
	def _suffixes(self):
		try:
			return self.__suffixes
		except AttributeError:
			self.__suffixes = suffixes = map(itemgetter(2), self.__fields__)
			return suffixes
		

class CLITool(object):
	logger = logging.getLogger("bonfire.cli")
		
	description = "BonFIRE command line client"
	
	default_uri = "https://api.bonfire-project.eu"
	
	infrastructure_uris = (
		("production", default_uri),
		("qualification", "https://api.qualification.bonfire-project.i2cat.net"), 
		("integration", "https://api.integration.bonfire.grid5000.fr")
	)
	
	available_actions = ("show", "list", "create", "update", "delete")
	
	if os.name == "nt":
		config_locations = [
			(expandvars("%APPDATA%\\bonfire"), "globalconfig"),
			expanduser("~\\.bonfire"),
			(expanduser("~\\bonfire"), "userconfig"),
		]
	else:
		if os.path.isdir("/etc/default"):
			config_locations = [
				"/etc/bonfire",
				("/etc/default/bonfire", "globalconfig"),
			]
		else:
			config_locations = [
				("/etc/bonfire", "globalconfig"),
				"/etc/default/bonfire",
			]
			
		if os.path.isdir(expanduser("~/.config")):
			config_locations += [
				expanduser("~/.bonfire"),
				(expanduser("~/.config/bonfire"), "userconfig"),
			]
		else:
			config_locations += [
				(expanduser("~/.bonfire"), "userconfig"),
				expanduser("~/.config/bonfire"),
			]
	
	out = sys.stdout
	
	_read_config_locations = []
	
	def __init__(self, name = None, *args, **kw):
		super(CLITool, self).__init__(*args, **kw)
	
		self.__name = name or sys.argv[0]
		
	@property
	def broker(self):
		try:
			return self.__broker
		except AttributeError:
			broker = self.__broker = Broker(**self._get_brokerargs())
			return broker 
		
	def _get_known_uri(self, key):
		self.logger.debug("Resolving infrastructure key %s", key)
		k = key.lower()[1:]
		for name, uri in self.infrastructure_uris:
			if name.lower().startswith(k):
				self.logger.debug("Resolved infrastructure key %s as %s", key, uri)
				return uri
		raise ConfigurationError("Failed to resolve infrastructure key %s", key)
		
	def _get_known_config_location(self, key):
		self.logger.debug("Resolving config location %s", key)
		k = key.lower()[1:]
		for entry in self.config_locations:
			if isinstance(entry, (tuple, list)) and len(entry) >= 2:
				if entry[1].lower().startswith(k):
					self.logger.debug("Resolved config location %s as %s", key, entry[0])
					return entry[0]
		raise ConfigurationError("Failed to resolve config location %s", key)
	
	def _get_config_locations(self):
		result = []
		for entry in self.config_locations:
			if isinstance(entry, (tuple, list)) and len(entry) >= 2:
				result.append(entry[0])
			else:
				result.append(entry)
		return result
		
	def _get_brokerargs(self):
		try:
			return self.__brokerargs
		except AttributeError:
			self.__brokerargs = brokerargs = {}
			
			for attr, arg in ( ("broker_uri", "url"), ):
				v = getattr(self.__basic_args, attr)
				if v:
					if v.startswith("%"):
						v = self._get_known_uri(v)
					brokerargs[arg] = v
					
			config = self.__get_global_config()
			
			if self.__basic_args.configfile:
				config = config.copy()
				self.__get_config_file(self.__basic_args.configfile, config)
				
			for attr, arg in (("BONFIRE_URI", "url"), ):
				v = config.get(attr)
				if v:
					brokerargs.setdefault(arg, v)
			
			brokerargs.setdefault("url", self.default_uri)
			
			username = self.__basic_args.username
			password = self.__basic_args.password
			
			if username is None:
				creds = config.get("BONFIRE_CREDENTIALS")
				if creds:
					username, _, pw = creds.partition(":")
					if username and pw and password is None:
						password = pw
				
			if (username is not None and password is None) or self.__basic_args.prompt:
				try:
					password = getpass("BonFIRE password: ")
				except EOFError:
					raise KeyboardInterrupt()
				
			brokerargs["username"] = username
			brokerargs["password"] = password
			print brokerargs
			return brokerargs
			
	def __call__(self, args = None):
		for a in args:
			if not a.startswith("-"):
				add_help = False
				break
		else:
			add_help = True
			
		#each tool/command combination has different option. We first create 
		#a basic parser object that will parse the command the user selected
		#as well as common options.
		common_parser = ArgumentParser(description = self.description, add_help = False, prog = self.__name, formatter_class = ArgumentDefaultsHelpFormatter)
		common_parser.add_argument("--version", action = 'version', version='%(prog)s ' + str(VERSION))
		common_parser.add_argument("-v", "--verbose", action="count" , default = 0,
					help = "Increase verbosity in output. This option can be specified multiple times.")
		common_parser.add_argument("-q", "--quiet", action = "store_true", help = "shut up on stdout")
		#common_parser.add_argument("-o", "--outfile", help = "redirect the output of 'show', 'list' and -s to this file.")
		common_parser.add_argument("-b", "--broker-uri", help = "URI of the BonFIRE broker. The magic values %%production, %%qualification and %%integration can be used to refer to well known URIs.")
		common_parser.add_argument("-f", "--configfile", help = "Location of configuration file")
		common_parser.add_argument("-u", "--username", help = "BonFIRE username")
		common_parser.add_argument("-p", "--password", help = "BonFIRE password. Will be prompted for if unavailable. WARNING: Arguments specified on the command line are on most systems obtainable by other processes. The use of this option is therefore strongly discouraged.")
		common_parser.add_argument("-m", "--prompt", action = "store_true", help = "Always prompt for a password, even when one is available through other sources.")
		#common_parser.add_argument("--ganja", action = "store_true", help = "Relax. Don't perform even the most basic input validation.")
		#common_parser.add_argument("--paranoid", action = "store_true", help = "Perform a GET on any ID encountered before using it in OCCI. Note that this will significantly slow down operations.")

		basic_parser = ArgumentParser(description = self.description, add_help = add_help, prog = self.__name, formatter_class = ArgumentDefaultsHelpFormatter, parents = (common_parser, ))
		
		basic_parser.add_argument("action", choices = [ "info" ] + list(self.available_actions))

		try:
			basic_args, _remaining = basic_parser.parse_known_args(args)
		except SystemExit:
			return
		
		self.__basic_args = basic_args
		
		try:
			# set logging level of root logger
			if basic_args.verbose:
				logging.getLogger().setLevel(basic_args.verbose > 1 and logging.DEBUG or logging.INFO)
				
				#replace the default formatter with something more verbose if -vv is given
				if basic_args.verbose > 1:
					debug_formatter = logging.Formatter('[%(name)s] %(levelname)s (%(filename)s:%(lineno)s): %(message)s')
					_logging_handler.setFormatter(debug_formatter)
			
			action = basic_args.action
			
			#we now know the action chosen and create an action specific parser 
			action_parser = ArgumentParser(description = self.description, prog = self.__name + " " + action, formatter_class = ArgumentDefaultsHelpFormatter, parents = (common_parser, ))
			action_parser.add_argument(action, help = SUPPRESS)
			
			#first add some generic options that apply to all tools
			if action == "info":
				action_parser.add_argument("-n", "--nopurge", action = "store_true", help = "Show plaintext passwords in output Note that plaintext passwords will always be written when writing config format output to a file.")
				action_parser.add_argument("-t", "--format", choices = ("plain", "config"), help = "Choose to write output either plain human readable or in a way that is suitable for use as config file. Defaults to config format when outputting to a known config location and to plain format in all other cases.")
				action_parser.add_argument("-o", "--outfile", help = "Write output to this file. When outputting in config file format (--format config), the magic values %%globalconfig and %%userconfig can be used to refer to the well known config file location.")
				action_parser.add_argument("-r", "--force", action = "store_true", help = "Force execution even when trying to overwrite a file or trying to write plain output to a known config file.")
			elif action not in ("show", "list"):
				
				action_parser.add_argument("-s", "--show", dest = "_print", action = "store_true", help = "print requests to stdout before sending them to the broker.")
				action_parser.add_argument("-d", "--dryrun", action = "store_true", help = "don't actually send requests to the broker. Implies -s unless -q is given.")
		
				if action == "create":
					action_parser.add_argument("-G", "--group", action = "append", help = "A number of groups.")
					action_parser.add_argument("name")
			else:
				action_parser.add_argument("-t", "--format", choices = ("plain", "xml", "csv"), default = "plain", help = "Format in which to show output.")
				action_parser.add_argument("-n", "--num", type = int, default = 1, help = "Number of times to retrieve information. Set to 0 to poll indefinitely.")
				action_parser.add_argument("-d", "--delay", type = float_gtz, default = 5, help = "Time to sleep between polling attempts in seconds.")
				action_parser.add_argument("-k", "--keep-going", action = 'store_true', help = "Keep going in face of errors encountered during polling.")
				action_parser.add_argument("-a", "--no-labels", action = "store_true", help = "Do not show field labels in csv and plain output.")
				action_parser.add_argument("-r", "--no-decorations", action = "store_true", help = "Suppress decorations in plain output.")
				action_parser.add_argument("-s", "--separator", type = separator, help = "Separator to use in csv and plain output. Defaults to ',' for CSV output and '|' for plain output.")

				if action == "list": 
					action_parser.add_argument("-e", "--details", action = "store_true", help = "Include additional information in output.")
					
			#let the specific tool add any specific options
			self._get_arg_parser(action, action_parser)
			
			try:
				action_args = self._parse_action_args(args, action_parser)
			except SystemExit:
				return
			
			self.logger.debug("Running action: %s", action)
						
			#handle the action
			result = self._action(action, action_args)
			
			#handle the actions result
			if action == "info":
				outfile = self.out
				
				if action_args.outfile:					
					if action_args.format != "config" and action_args.outfile in self._get_config_locations() and not action_args.force:
						raise ConfigurationError("Refusing to write non config format output to config file '%s'." % (action_args.outfile, ))
					
					self.logger.info("Writing output in %s format to %s", action_args.format, action_args.outfile)
					
					if not action_args.force and exists(action_args.outfile):
						raise CLIError("Refusing to overwrite file '%s'" % (action_args.outfile, ))
					
					outfile = open(action_args.outfile, "w")
				
				try:
					for line in result:
						outfile.write(line + "\n")
				finally:
					if outfile != sys.stdout:
						outfile.close()
			elif action in ("update", "create"):
				self._request(action == "update" and "PUT" or "POST", result[0], result[1], action_args)
			elif action in ("show", "list"):
				num = action_args.num
				
				if num <= 0:
					self.logger.info("Polling indefinitely.")
				
				while num > 0 or action_args.num <= 0:
					try:
						getattr(self, "_" + action + "_" + action_args.format)(result, self.out, action_args)
					except Exception, e:
						if not action_args.keep_going or action_args.num == 1:
							raise
						if self.logger.isEnabledFor(logging.DEBUG):
							self.logger.exception("Error retrieving data")
						else:
							self.logger.error(e)
					if num:
						num -= 1
						if num:
							self.logger.debug("Will poll another %s times.", num)
					if (num or action_args.num <= 0) and action_args.delay:
						self.logger.info("Sleeping %ss before polling for information again.", action_args.delay)
						sleep(action_args.delay)
			elif action == "delete":
				if action_args._print or (action_args.dryrun and not action_args.quiet):
					self.out.write("DELETE %s\n" % (result, ))
				if action_args.dryrun:
					self.logger.info("dry run. not calling broker.")
				else:
					self.broker.delete(result)
					if not action_args.quiet:
						self.out.write("Deleted: %s\n" % (result, ))
			else:
				self._handle_result(action, action_args, result)
		finally:
			del self.__basic_args
			
	def _parse_action_args(self, args, parser):
		return parser.parse_args(args)
					
	def _action(self, action, args):
		f = getattr(self, "_action_" + action)
		return f(args)
	
	def _handle_result(self, args, result):
		pass
	
	def _get_details(self, r):
		return r
	
	def _action_info(self, args):
		brokerargs = self._get_brokerargs()
		brokerargs.setdefault("uri", brokerargs.pop("url", None))
		
		
		if args.outfile and args.outfile.startswith("%"):
				args.outfile = self._get_known_config_location(args.outfile)
				
		if not args.format:
			if args.outfile in self._get_config_locations():
				args.format = "config"
			else:
				args.format = "plain"

		if args.format == "config" and args.outfile:
			args.nopurge = True
		
		pw = brokerargs.get("password")
		if pw and not args.nopurge:
			pw = brokerargs["password"] = "*" * len(pw) 
		if args.format == "config":
			result = [ 'BONFIRE_URI="%s"' % ( brokerargs["uri"], ) ]
			username = brokerargs.get("username")
			if username or pw:
				result.append('BONFIRE_CREDENTIALS="%s:%s"' % (username or "", pw or ""))
		else:
			import platform
			
			try:
				ETREE_VERSION = bonfire.broker.occi.etree.ETREE_VERSION
			except AttributeError:
				ETREE_VERSION = "(unknown version)"
				
			archinfo = platform.architecture()
			
			result =  [ "BonFIRE %s: %s" % (k.capitalize(), v or "<n/a>") for k, v in brokerargs.items() ]
			result += [ 
				"OS: %s %s %s (%s)" % (platform.system(), platform.release(), platform.version(), os.name),
				"libc: " + ' '.join(platform.libc_ver()), 
				"Python: %s %s (%s %s %s %s)" % (platform.python_implementation(), platform.python_version(), sys.executable, platform.python_compiler(), archinfo[0], archinfo[1]),
				"bonfire-python: %s" % (bonfire.version.VERSION, ),
				"bonfire-cli: %s" % (VERSION, ),
				"ElementTree: %s %s" % (bonfire.broker.occi.etree.ElementTree.__module__, ETREE_VERSION)
			]
			
			#for filename, error in self._read_config_locations:
			#	result.append("Config Location: %s - %s" % (filename, error or "<read>"))
			
		return result
		
	def _get_arg_parser(self, action, parser):
		pass
			
	def _request(self, method, uri, data, args):
		if args._print or (args.dryrun and not args.quiet):
			self.out.write("%s %s\n%s" % (method, uri, data))
		if args.dryrun:
			self.logger.info("dry run. not calling broker.")
		else:
			if args.verbose:
				now = time()
			result = self.broker.occi(method, uri, data, validate = False)
			if not args.quiet:
				self.out.write("%s: %s\n" % (method == "POST" and "Created" or "Updated", result, ))
			if args.verbose:
				self.logger.info("Request %s %s finished in %.4fs", method, uri, time() - now)
			
	@staticmethod
	def __get_config_file(name, config):
		CLITool.logger.debug("Reading configuration file %s", name)
		try:
			with open(name, "rU") as f:
				CLITool._read_config_locations.append((name, None))
				for line in f:
					line = line.rstrip("\n").lstrip()
					if not line.startswith('#'):
						name, sep, value = line.partition("=")
						if sep:
							config[name.strip()] = value.strip().strip('"')
		except Exception, e:
			CLITool.logger.debug("Error reading %s: %s", name, e)
			CLITool._read_config_locations.append((name, str(e)))
			
	@staticmethod
	def __get_global_config():
		try:
			return CLITool.__global_config
		except AttributeError:
			config = CLITool.__global_config = {}
			for entry in CLITool.config_locations :
				if isinstance(entry, (tuple, list)):
					CLITool.__get_config_file(entry[0], config)
				else:
					CLITool.__get_config_file(entry, config)
				
			return config
		
	def _log_exception(self, msg):
		if self.logger.isEnabledFor(logging.DEBUG):
			self.logger.exception(msg)
		else:
			self.logger.error(msg)
		
	def _handle_prefetch_error(self, e, r, resources):
		self._log_exception("Failed to fetch resource info for '%s': %s" % (r.id, e))
		
	def _list_xml(self, resources, out, args):
		if not resources:
			out.write("<items/>\n")
		else:
			out.write("<items>\n")
			for r in resources:
				lines = r.xml.split("\n")
				map("  ".__add__, lines)
				xml = "\n".join(lines)
				out.write(xml)
			out.write("</items>\n")
			
	def _list_csv(self, resources, out, args):
		from csv import writer
		
		headers = ["ID", "Name"]
		
		writer = writer(out, delimiter=args.separator or ",")
		
		if args.details and resources:
			formatter = self._get_formatter(resources[0], args)
			headers.extend(formatter._labels)
			
		if not args.no_labels:
			writer.writerow(headers)
			
		for r in resources:
			row = [ r.id, r.name ]
			
			if args.details:
				row += map(itemgetter(1), formatter.format_list_details(self._get_details(r))[2:])
			
			writer.writerow(row)
		
	def _list_plain(self, resources, out, args):
		print "0000000000"  
		print resources
		print "AAAAAAAAAA"
		headers = ["ID", "Name"]
		if args.no_decorations:
			vert_sep = ""
		else:
			vert_sep = args.separator or "|"
		
		if args.details and resources:
			from bflocation import LocationFormatter
			formatter = self._get_formatter(resources[0], args)
			if not isinstance(formatter, LocationFormatter):
				headers.append("Group")
			headers.extend(formatter._labels)
		
		if not args.no_labels:
			maxlens = map(len, headers)
		else:
			maxlens = [ 0 for _ in headers ]
			
		for r in resources:
			if len(r.id) > maxlens[0]:
				maxlens[0] = len(r.id)
			if len(r.name) > maxlens[1]:
				maxlens[1] = len(r.name)
				
		if args.details:
			rows = {}
			
			for i, name in enumerate(formatter._labels, 2):
				if len(name) > maxlens[i]:
					maxlens[i] = len(name)
					
			print resources
			resources = self.broker.prefetch(resources, self._handle_prefetch_error)
			
			for r in resources:
				if r.needs_prefetching():
					rows[r.id] = [ "" for _ in formatter._names ]
				else:
					try:
						vals = formatter.format_list_details(self._get_details(r))[2:]
						self.logger.error(headers)
						self.logger.error(maxlens)
						self.logger.error(vals)
						for i, (_, val) in enumerate(vals, 2):
							print val
							maxlens[i] = max(maxlens[i], len(val))
						rows[r.id] = map(itemgetter(1), vals)
					except BonfireError, e:
						self._log_exception("Failed to get details for '%s': %s." % (r.id, e))
						rows[r.id] = [ "" for _ in formatter._names ]
			
		if not args.no_decorations:
			separator = ("=" * (sum(maxlens) + (3 * len(maxlens)) + 1)) + "\n"	
			out.write(separator)
		
		if not args.no_labels:
			headers = [ s.ljust(maxlens[i]).center(maxlens[i] + 2) for i, s in enumerate(headers) ]
			out.write(vert_sep + vert_sep.join(headers) + vert_sep + "\n")
		
			if not args.no_decorations:
				out.write(separator)

		for r in resources:
			out.write(vert_sep + r.id.ljust(maxlens[0]).center(maxlens[0] + 2) + vert_sep + r.name.ljust(maxlens[1]).center(maxlens[1] + 2) + vert_sep)
			
			if args.details:
				for i, val in enumerate(rows[r.id], 2):
					out.write(val.ljust(maxlens[i]).center(maxlens[i] + 2) + vert_sep)
			
			out.write('\n')
	
		if not args.no_decorations:
			out.write(separator)
		
	def _get_list_headers(self):
		return ()
		
	def _show_xml(self, entity, out, args):
		xml = entity.xml
		out.write(xml)
		if not xml.endswith("\n"):
			out.write("\n")
			
	def _show_csv(self, entity, out, args):
		from csv import writer
		
		writer = writer(out, delimiter=args.separator or ",")
		formatter = self._get_formatter(entity, args)
		
		if not args.no_labels:
			writer.writerow(["ID", "Name"] + formatter._labels)
		
		writer.writerow(map(itemgetter(1), formatter(entity)))
			
	def _show_plain(self, entity, out, args):
		formatter = self._get_formatter(entity, args)
		vals = formatter(entity)
		for label, value in vals:
			if not args.no_labels:
				out.write(label)
				if not args.no_decorations:
					out.write(":")
				out.write(" ")
			out.write(value)
			out.write("\n")
			
	def _get_formatter(self, entity, args):
		return Formatter()
	
	@classmethod
	def run_once(cls):
		try:
			sys.stdout = sys.stderr
			cls.logger.debug("Running " + cls.__name__)
			tool = cls()
			tool(sys.argv[1:])
		except ConfigurationError, e:
			cls.logger.error(str(e))
			sys.exit(2)
		except BonfireError, e:
			cls.logger.error(str(e))
			sys.exit(1)
		except (KeyboardInterrupt, SystemExit), e:
			cls.logger.warn("Interrupted by %s.", e.__class__.__name__)
			sys.exit(3)
		except Exception, e:
			cls.logger.exception("Internal Error")
			sys.exit(100)
		else:
			sys.exit(0)
