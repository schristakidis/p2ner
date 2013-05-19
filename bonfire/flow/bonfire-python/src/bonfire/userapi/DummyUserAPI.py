'''
Created on 24.03.2011

@author: kca
'''

from UserAPI import UserAPI
from User import User
from exc import UnknownUserError

class DummyUserAPI(UserAPI):
    def __init__(self, *args, **kw):
        self.__users = { 
                "dummy": User(
                    userapi = self,
                    uid = "dummy",
                    fields = {
                        "fullname": "a dummy",
                        "uid_number": 42,
                        "groups": [ 36, 42 ],
                        "home_directory": "/home/dummy",
                        "shell": "/bin/sh",
                } )}
        
    def list_users(self):
        return self.__users.values()
    
    def get_user(self, uid):
        try:
            return self.__users[uid]
        except KeyError:
            raise UnknownUserError(uid)
        
    def persist(self, e):
        assert(isinstance(e, User))
        self.__users[e.uid] = e
        e._userapi = self
        assert(e.is_persistent)
    