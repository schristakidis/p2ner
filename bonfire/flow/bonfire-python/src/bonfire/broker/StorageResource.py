'''
Created on 25.11.2010

@author: kca
'''

from Resource import Resource  

class StorageResource(Resource):	
	__fields__ = (
		("user_id", str),
		("type", str), 
		("size", int),
		("fstype", str),
		("public", bool),
		("persistent", bool),
		("state", str)
	)
	
	@property
	def ready(self):
		return self.state and self.state.lower() == "ready"
	
	@property
	def is_datablock(self):
		return self.type and self.type.lower() in ("datablock", "shared")
	
	@property
	def is_os_image(self):
		return not self.is_datablock
	
	@property
	def is_public(self):
		return self.public
	
	@property
	def is_official(self):
		return self.is_public and self.user_id in ("admin", "oneadmin", "one-admin") or self.name.lower().startswith("bonfire")
