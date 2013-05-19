from UserAPIEntity import UserAPIEntity

class Group(UserAPIEntity):
	'''
	classdocs
	'''
	
	__fields__ = (
		("gid_number", int),
		("uids", [ int ])
	)
	
	__ou__ = "Groups"
	__object_classes__ = ( 'posixGroup', )
	__id_attribute__ = "cn"

	def __init__(self, gid, *args, **kw):
		super(Group, self).__init__(*args, **kw)
		self.__gid = gid

	def get_gid(self):
		return self.__gid
	gid = property(get_gid)
	id = gid
	
	def _set_gid(self, gid):
		self.__uid = gid
	_uid = property(get_gid, _set_gid)
	
	def get_users(self):
		assert(self.is_persistent)
		if not self.uids:
			return ()
		return self._userapi.list_users(self.uids)
	users = property(get_users)
	
	def get_admins(self):
		assert(self.is_persistent)
		return self._userapi.list_users(filter = ("administered_group_ids", self.gid))
	admins = property(get_admins)
	
	def get_has_admin(self):
		return bool(self.get_admins())
	has_admin = property(get_has_admin)
	
	def add_user(self, user):
		user = getattr(user, "uid", user)
		if user not in self.uids:
			self.uids.append(user)
		
	def remove_user(self, user):
		user = getattr(user, "uid", user)
		try:
			self.uids.remove(user)
		except ValueError:
			pass
		
	