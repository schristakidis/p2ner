from string import lowercase
from bonfire.broker.federica import Interface, NetworkLink, FedericaEndpoint

def context_item(val):
	name, sep, value = val.partition("=")
	if not name or not sep:
		raise ValueError("Illegal context item: '%s'" % (val, ))
	return (name, value)

context_item.__name__ = "Context"
	
def location_id(val):
	val = val.rstrip("/")
	if not val.startswith("/"):
		prefix, _, suffix = val.partition("-")
		
		for c in prefix + suffix:
			if c not in lowercase:
				raise ValueError("Invalid location ID: '%s'" % (val, ))
			
		val = "/locations/" + val
	return val

def resource_id(val):
	return val.rstrip("/")

resource_id.__name__ = "Resource ID / name"

def experiment_id(val):
	val = val.rstrip("/")
	if not val.startswith("/"):
		try:
			int(val)
		except (TypeError, ValueError):
			raise ValueError("Invalid experiment ID: '%s'" % (val, ))

		val = "/experiments/" + val
	return val

experiment_id.__name__ = "Experiment ID"

def ip_address(val):
	if len(val.split(".")) != 4:
		raise ValueError(val)
	
	from socket import inet_aton, error

	try:
		inet_aton(val)
	except error:
		raise ValueError(val)
	
	return val
	
ip_address.__name__ = "IP Address"

def int_gtz(val):
	val = int(val)
	if val < 0:
		raise ValueError(val)
	return val

def float_gtz(val):
	val = float(val)
	if val < 0.0:
		raise ValueError(val)
	return val

boolean_choices = ("true", "false", "yes", "no", "1", "0", "t", "f")

def parse_bool(s):
	return s in ("true", "yes", "1", "t")

def lossrate(val):
	val = float(val)
	if val < 0.0 or val > 1.0:
		raise ValueError(val)
	return val

def latency(val):
	val = int(val)
	if val and val < 2:
		raise ValueError(val)
	return val

def bandwidth(val):
	val = int(val)
	if val < 1 or val > 1000:
		raise ValueError(val)
	return val

_ip = 1
def interface(val):
	global _ip
	
	token = val.split(",") 
	if len(token) > 4:
		raise ValueError("to many parameters")

	if len(token) < 2:
		raise ValueError("a least two parameters needed")
	
	name = token[0]
	phys_if = token[1]
	#TODO: check name and if for validity

	if len(token) >= 3:
		ipa = ip_address(token[2])
	else:
		ipa = "192.168.%s.1" % (_ip, )
		_ip += 1

	netmask = "255.255.255.0"
	if len(token) >= 4:
		netmask = ip_address(token[3])

	return Interface( name, phys_if, ipa, netmask )

def network_link(val):
	token = val.split(",")
	if len(token) != 4:
		raise ValueError(val)
	link = NetworkLink()
	link.endpoint = [
		FedericaEndpoint(token[0], token[1]),
		FedericaEndpoint(token[2], token[3]),
	]
	return link

def cidr_prefix(val):
	val = int_gtz(val)
	if val > 32:
		raise ValueError(val)
	return val

def duration(val):
	try:
		return int_gtz(val)
	except ValueError:
		import re
		result = re.match(r"^(?:(\d+?)d[a-z]*)?(?:(\d+?)h[a-z]*)?(?:(\d+?)m[a-z]*)?(?:(\d+?)(?:s[a-z]*)?)?$", val, re.I)
		if result is None:
			raise ValueError(val)
		days, hours, mins, secs = result.groups()
		secs = secs and int(secs) or 0
		if mins:
			secs += int(mins) * 60
		if hours:
			secs += int(hours) * 60 * 60
		if days:
			secs += int(days) * 60 * 60 * 24
		return int_gtz(secs)

def separator(val):
	if len(val) != 1:
		raise ValueError("Separator must be a 1-character string.")
	return val