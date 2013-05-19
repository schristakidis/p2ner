from bonfire.exc import BonfireError

class CLIError(BonfireError):
	pass

class ConfigurationError(CLIError):
	pass 