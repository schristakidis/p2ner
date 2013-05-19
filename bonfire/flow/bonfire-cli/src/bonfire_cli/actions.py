from argparse import Action
from exc import ConfigurationError
from string import lowercase
import re

class CLIToolAction(Action):
	def __init__(self, option_strings, dest, nargs=None, const=None, default=None, type=None,
				 choices=None, required=False, help=None, metavar=None, *args, **kw):
		if nargs not in (1, "?", None):
			raise ValueError("nargs must be 1, '?' or None")
		super(CLIToolAction, self).__init__(option_strings=option_strings, dest=dest, nargs=nargs, const=const, 
			default=default, type=type, choices=choices, required=required,	help=help, metavar=metavar, *args, **kw)
		
class ExperimentIDAction(CLIToolAction):
	def __call__(self, parser, namespace, values, option_string=None):
		if values == "":
			raise ConfigurationError("Invalid experiment ID: ''")
		
		if values:
			values = values.rstrip("/")
			if not values.startswith("/"):
				try:
					int(values)
				except (TypeError, ValueError):
					raise ConfigurationError("Invalid experiment ID: '%s'" % (values, ))
	
				values = "/experiments/" + values
		setattr(namespace, self.dest, values)
	
class LocationIDAction(CLIToolAction):
	def __call__(self, parser, namespace, values, option_string=None):
		if values == "":
			raise ConfigurationError("Invalid location ID: ''")
		
		if values:
			values = values.rstrip("/")
			if not values.startswith("/"):
				prefix, _, suffix = values.partition("-")
				
				for c in prefix + suffix:
					if c not in lowercase:
						raise ConfigurationError("Invalid location ID: '%s'" % (values, ))
					
				values = "/locations/" + values
		setattr(namespace, self.dest, values)
		
class ResourceIDAction(CLIToolAction):
	def __call__(self, parser, namespace, values, option_string=None):
		if values == "":
			raise ConfigurationError("Invalid resource ID: ''")
		if values:
			values = values.rstrip("/")
		setattr(namespace, self.dest, values)

class IPAction(CLIToolAction):
	def __call__(self, parser, namespace, values, option_string=None):
		regex = r'^?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?$'
		
		if not re.match(regex, values):
			raise ConfigurationError("Not a valid IP Address: '%s'" % (values, ))
		
		setattr(namespace, self.dest, values)
