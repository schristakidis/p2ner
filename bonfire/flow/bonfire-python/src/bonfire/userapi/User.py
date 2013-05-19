'''
Created on 21.02.2011

@author: kca
'''
from UserAPIEntity import UserAPIEntity

class User(UserAPIEntity):
	'''
	classdocs
	'''
	
	__fields__ = (
		("fullname", unicode),
		("uid_number", int),
		("gidNumber", int),
		("home_directory", str),
		("shell", str),
		("public_key", [ str ]),
		("password", str),
		("email", str),
		("sn", str),
		("administered_group_ids", [ str ]),
		#("nationality", str),
		("country", str),
		("organisation", str),
		("city", str),
		("street", str),
		("postal", str),
		("phone", str),
		("nationality", str)
	)
	
	__ou__ = "People"
	__object_classes__ = ( 'top', 'posixAccount', 'inetOrgPerson', "ldapPublicKey", )
	__id_attribute__ = "uid"

	def __init__(self, uid, *args, **kw):
		super(User, self).__init__(*args, **kw)
		self.__uid = uid

	def get_uid(self):
		return self.__uid
	uid = property(get_uid)
	id = uid
	
	def _set_uid(self, uid):
		self.__uid = uid
	_uid = property(get_uid, _set_uid)
	
	@property
	def groups(self):
		assert self.is_persistent
		return self._userapi.list_groups(self)
	
	@property
	def administered_groups(self):
		assert self.is_persistent
		return self._userapi.list_groups(self, gids = self.administered_group_ids)
	
	def is_admin_for(self, group):
		return getattr(group, "gid", group) in self.administered_group_ids
	
	def revoke_group_admin(self, group):
		if not self.is_admin_for(group):
			return False
		self.administered_group_ids.remove(getattr(group, "gid", group))
		return True
	
	def grant_group_admin(self, group):
		if self.is_admin_for(group):
			return False
		self.administered_group_ids.append(getattr(group, "gid", group))
		return True
		