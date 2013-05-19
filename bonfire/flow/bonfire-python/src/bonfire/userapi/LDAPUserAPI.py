'''
Created on 24.03.2011

@author: kca
'''

from UserAPI import UserAPI
from User import User
from exc import UnknownUserError, WeAreFull, CommunicationError, OperationalError
import ldap
from ldapurl import LDAPUrl
from ldap.dn import escape_dn_chars
from hashlib import sha1
from base64 import b64encode
from os import urandom as random
from bonfire.userapi.Group import Group

class LDAPUserAPI(UserAPI):   
	__map = {
		"fullname": "cn",
		"uid_number": "uidNumber",
		"home_directory": "homeDirectory",
		"shell": "loginShell",
		"public_key": "sshPublicKey",
		"password": "userPassword",
		"email": "mail",
		"gid_number": "gidNumber",
		"uids": "memberUid",
		"administered_group_ids": "o",
		"organisation": "postalAddress",
		"country": "st",
		"city": "l",
		"street": "street",
		"postal": "postalCode",
		"phone": "homePhone",
		"nationality": "preferredLanguage"
	}
	
	UID_MIN = 2001
	UID_MAX = 3000
	
	GID_MIN = 2001
	GID_MAX = 3000
		
	def __init__(self, uri, bindname = None, password = None, cert_file = None, cert_key = None, cacert_file = None, require_cert = True, uid_min = None, uid_max = None, gid_min = None, gid_max = None, *args, **kw):
		super(LDAPUserAPI, self).__init__(*args, **kw)
		self.__url = LDAPUrl(uri)
		self.__dn = self.__url.dn
		self.__connection = None
		self.__bindname = bindname and bindname or escape_dn_chars(self.__url.who) + "," + self.__dn
		self.__password = password and password or self.__url.cred
		
		if cert_file:
			ldap.set_option(ldap.OPT_X_TLS_CERTFILE, cert_file)
			
		if cert_key:
			ldap.set_option(ldap.OPT_X_TLS_KEYFILE, cert_key)
			
		if cacert_file:
			ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, cacert_file)
		
		if not require_cert:
			ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_NEVER)
				
		self.__uid_min = uid_min or self.UID_MIN
		self.__uid_max = uid_max or self.UID_MAX
		self.__gid_min = gid_min or self.GID_MIN
		self.__gid_max = gid_max or self.GID_MAX

	def _get_connection(self):
		if self.__connection is None:
			con = self._make_connection()
			self.logger.debug("LDAP bind()")
			con.simple_bind_s(self.__bindname, self.__password)
			self.__connection = con
			
		return self.__connection
	
	def _make_connection(self):
		return ldap.initialize(self.__url.initializeUrl())
		
	def list_users(self, uids = None, filter = ("uid", "*")):
		users = [ self.__make_entity(data, User) for data in self.__search(filter[1], filter[0]) ]
		if uids:
			users = [ u for u in users if u.uid in uids ]
		return users
	
	def list_groups(self, user = None, gids = None, filter = ("cn", "*")):
		if user:
			filter = ("memberUid", getattr(user, "id", user))
		groups = [ self.__make_entity(data, Group) for data in self.__search(filter[1], filter[0], "Groups") ]
		if gids:
			groups = [ g for g in groups if g.gid in gids ]
		return groups
	
	def get_user(self, uid):
		res = self.__search(uid)
		assert(isinstance(res, (tuple, list)))
		if not res:
			raise UnknownUserError(uid)
		if len(res) > 1:
			self.logger.warn("%d entries found for %s. Using first entry. (%s)" % (len(res), uid, res))
		return self.__make_entity(res[0], User)
	
	def get_group(self, gid):
		res = self.__search(gid, "cn", "Groups")
		assert(isinstance(res, (tuple, list)))
		if not res:
			raise UnknownUserError(gid)
		if len(res) > 1:
			self.logger.warn("%d entries found for %s. Using first entry. (%s)" % (len(res), gid, res))
		return self.__make_entity(res[0], Group)
	
	def email_exists(self, email):
		res = self.__search(email, "mail")
		return len(res) != 0
	
	def __search(self, uid, attribute = "uid", ou = "People"):
		try:
			return self.__ldap_op("search", "ou=" + ou + "," + self.__dn, ldap.SCOPE_SUBTREE, "(%s=%s)" % (self.__map.get(attribute, attribute), uid, ))
		except ldap.LDAPError, e:
			raise CommunicationError("LDAP search failed: " + str(e[0]["desc"]))
		
	def __ldap_op(self, opname, *args):
		try:
			con = self._get_connection()
			try:
				#self.logger.debug("Executing %s with %s" % (opname, args))
				return getattr(con, opname + "_s")(*args)
			except ldap.SERVER_DOWN:
				con.unbind_s()
				try:
					self.__connection = None
					con = self._get_connection()
					#self.logger.debug("Retrying %s with %s" % (opname, args))
					return getattr(con, opname + "_s")(*args)
				except ldap.SERVER_DOWN, e:
					raise CommunicationError("LDAP %s failed: %s" % (opname, str(e[0]["desc"])))
		except ldap.LDAPError, e:
			if isinstance(e[0], dict):
				msg = e[0]["desc"]
			else:
				msg = str(e)
				
			self.logger.exception("LDAP %s failed" % (opname, ))
			raise OperationalError("LDAP %s failed: %s" % (opname, msg))
	
	def check_password(self, uid, password):
		if not password:
			return False
		
		if hasattr(uid, "uid"):
			uid = uid.uid
		
		bindname = self.__make_dn(uid, "uid", "People")
		con = self._make_connection()
		try:
			con.simple_bind_s(bindname, password)
		except ldap.INVALID_CREDENTIALS:
			con.unbind()
			return False
		except ldap.LDAPError, e:
			raise CommunicationError("LDAP bind failed: " + str(e[0]["desc"]))
		
		con.unbind()
		
		return True
			
	def _find_uid_number(self):
		all = set( [ str(u.uid_number) for u in self.list_users() ] )
		
		for id in xrange(self.__uid_min, self.__uid_max): 
			if str(id) not in all:
				return id
			
		raise WeAreFull("No unused uid found in range %d - %d" % (self.__uid_min, self.__uid_max))
	
	def _find_gid_number(self):
		all = set( [ str(g.gid_number) for g in self.list_groups() ] )
		
		for id in xrange(self.__gid_min, self.__gid_max): 
			if str(id) not in all:
				return id
			
		raise WeAreFull("No unused gid found in range %d - %d" % (self.__gid_min, self.__gid_max))
	
	def _encode(self, s):
		if not isinstance(s, str):
			s = unicode(s).encode("utf-8")
		return s
	
	def persist(self, entity):
		if not entity.is_persistent:
			self.assert_legal_uid(entity.id)
			entity._userapi = self
			
#			logger.debug( "Entity: %s" %entity)
			
			object_classes = list(entity.__object_classes__)
			if isinstance(entity, User):
				if entity.uid_number is None:
					entity.uid_number = self._find_uid_number()
				if not entity.public_key:
					object_classes.remove("ldapPublicKey")
				entity.sn = "Unused for R2"
			elif entity.gid_number is None:
				entity.gid_number = self._find_gid_number()
				
			add_record = [ ('objectclass', object_classes ), (entity.__id_attribute__, [ entity.id.encode("utf-8") ] ) ]
			add_record += [ ( self.__map.get(f, f), [ self._encode(getattr(entity, f)) ] ) for f, _ in entity.get_fields() if f not in ("gidNumber", "password") and getattr(entity, f) ]
			
			if  isinstance(entity, User):
				if entity.password:
					add_record.append( ( "userPassword", self.make_secret(entity.password) ) )
				add_record.append( ( 'gidNumber', entity.gidNumber and [ str(entity.gidNumber) ] or [ "2000" ] ) )
			
#			logger.debug("Add: %s   %s" %(self.__make_dn(entity.id, entity.__id_attribute__, entity.__ou__), add_record))
			self.__ldap_op("add", self.__make_dn(entity.id, entity.__id_attribute__, entity.__ou__), add_record)
		else:
			have_classes = set(entity._object_classes)
			object_classes = set(entity.__object_classes__)
			if isinstance(entity, User) and not entity.public_key:
				object_classes.remove("ldapPublicKey")

			mod_attrs = [ (ldap.MOD_ADD, "objectClass", m) for m in (object_classes - have_classes) ]
			mod_attrs += [ (ldap.MOD_DELETE, "objectClass", m) for m in (have_classes - object_classes) ]

			for f, t in entity.get_fields():
				if f not in ("gidNumber", "password"):
					val = getattr(entity, f)
					if isinstance(t, (list, tuple, set, frozenset)):
						new = set(val)
						old = set(entity._old[f])
						#self.logger.debug(new)
						#self.logger.debug(old)
						mod_attrs += [ (ldap.MOD_ADD, self.__map.get(f, f), self._encode(v)) for v in (new - old) ]
						mod_attrs += [ (ldap.MOD_DELETE, self.__map.get(f, f), self._encode(v)) for v in (old - new) ]
					else:
						
						in_old = bool(entity._old.get(f))
						if val:
							mod_attrs.append( ( in_old and ldap.MOD_REPLACE or ldap.MOD_ADD, self.__map.get(f, f), self._encode(val) ) )
						elif in_old:
							mod_attrs.append( (ldap.MOD_DELETE, self.__map.get(f, f), None) )
					
			if isinstance(entity, User) and entity.password:
				mod_attrs.append( ( ldap.MOD_REPLACE, "userPassword", self.make_secret(entity.password) ) )

			self.__ldap_op("modify", self.__make_dn(entity.id, entity.__id_attribute__, entity.__ou__), mod_attrs)

		entity._object_classes = tuple(object_classes)
		entity._init()

	def delete(self, uid):
		uid = getattr(uid, "uid", uid)
		try:
			groups = self.list_groups(user = uid)
			for group in groups:
				group.remove_user(uid)
				self.persist(group)
		except ldap.LDAPError, e:
			raise CommunicationError("LDAP remove group membership failed: " + str(e[0]["desc"]))
		try:
			self._get_connection().delete_s(self.__make_dn(uid, "uid", "People"))
		except ldap.LDAPError, e:
			raise CommunicationError("LDAP delete failed: " + str(e[0]["desc"]))
	delete_user = delete
		
	def delete_group(self, group):
		try:
			if not isinstance(group, Group):
				group = self.get_group(group)
			for u in group.admins:
				u.administered_group_ids.remove(group.gid)
				self.persist(u)
			self._get_connection().delete_s(self.__make_dn(group.gid, "cn", "Groups"))
		except ldap.LDAPError, e:
			raise CommunicationError("LDAP delete failed: " + str(e[0]["desc"]))
	
	def __make_entity(self, data, klass):
		id_attribute = klass.__id_attribute__
		cn, data = data	
		try:
			uid = data[id_attribute][0]
		except (IndexError, KeyError):
			self.logger.exception("Missing %s attribute in entry %s" % (id_attribute, cn, ))
			raise
		
		e = klass(uid, userapi = self)
		
		for name, type in klass.get_fields():
			if name != "password":
				ldapname = self.__map.get(name, name)
				try:
					value = data[ldapname]
				except KeyError:
					continue
				
				if not isinstance(type, (list, tuple, set, frozenset)):
					if value:
						if len(value) > 1:
							self.logger.warn("More than one entry received for attribute %s (%s) in item %s" % (name, value, cn))
						value = value[0]
						if name == "uid_number":
							value = int(value)
					else:
						value = None
				elif not isinstance(value, (list, tuple, set, frozenset)):
					value = [ value ]
					
				setattr(e, name, value)
			
		e._object_classes = tuple(data["objectClass"])
		e._init()
			
		return e
			
	def make_secret(self, password, salt = None):
		if not salt:
			salt = random(4)
		elif len(salt) != 4:
			raise ValueError(salt)
		if isinstance(password, unicode):
			password = password.encode("utf-8")
		h = sha1(password)
		h.update(salt)
		return "{SSHA}" + b64encode(h.digest() + salt)
		
	def __make_dn(self, uid, attribute, ou):
		return "%s=%s,ou=%s,%s" % (attribute, escape_dn_chars(uid), ou, self.__dn)
