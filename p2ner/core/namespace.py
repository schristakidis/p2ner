# -*- coding: utf-8 -*-

from collections import MutableMapping
from itertools import chain, imap
from weakref import ref
import inspect, pprint

class _globalNamespace(MutableMapping):
    def __init__(self, ns):
        self.__dict__['_ns'] = ref(ns)
        self.__dict__['_globalNS'] = [ns._localNS]
        if ns._parent_:
            self.__dict__['_globalNS'] += ns._parent_()._globalNS

    @property
    def root(self):
        return self._ns().root.g

    @property
    def l(self):
        return getattr(self, '_ns')()

    @property
    def g(self):
        return self

    def __getitem__(self, key):
        for ns in self._globalNS:
            if key in ns:
                break
        return ns[key]

    def __setitem__(self, key, value):
        for ns in self._globalNS:
            if key in ns:
                ns[key] = value
                return
        self._globalNS[0][key] = value

    def __delitem__(self, key):
        for ns in self._globalNS:
            if key in ns:
                del ns[key]
                return
        del ns[key]

    def __len__(self, len=len, sum=sum, imap=imap):
        return sum(imap(len, self._globalNS))

    def __iter__(self):
        return chain.from_iterable(self._globalNS)

    def __contains__(self, key, any=any):
        return any(key in ns for ns in self._globalNS)

    def __repr__(self, repr=repr):
        return ' -> '.join(imap(repr, self._globalNS))

    def __getattr__(self, name):
        if name == "_globalNS":
            raise AttributeError()
        for ns in self._globalNS:
            if name in ns:
                return ns[name]
        raise AttributeError()

    def __setattr__(self, name, value):
        if name in ["_ns", "_globalNS"]:
            raise AttributeError("Read only attribute: '%s'" % name)
        if name in self.__dict__:
            self.__dict__[name] = value
            return
        for ns in self._globalNS:
            if name in ns:
                ns[name] = value
                return
        self._globalNS[0][name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            del self.__dict__[name]
            return
        for ns in self._globalNS:
            if name in ns:
                del ns[name]
                return
        del ns[name]
from collections import Hashable
class Namespace(MutableMapping, Hashable):
    def __init__(self, parent=None):
        if parent:
            if not isinstance(parent, Namespace):
                raise TypeError
        try:
            self.__dict__['_parent_'] = ref(parent)
        except TypeError:
            self.__dict__['_parent_'] = None
        self.__dict__['_localNS'] = {}
        
    @property
    def parent(self):
        return self._parent
    
    @property
    def _parent(self):
        if self._parent_:
            return getattr(self, '_parent_')()
        return None

    @property
    def root(self):
        if not self._parent:
            return self
        return self._parent.root

    @property
    def g(self):
        return _globalNamespace(self)

    @property
    def l(self):
        return self

    @property
    def _globalNS(self):
        if not self._parent:
            return [self._localNS]
        return [self._localNS] + self._parent._globalNS

    def __getitem__(self, key):
        if key in self._localNS:
            return self._localNS[key]
        if self._parent:
            return self._parent[key]
        return self._localNS[key]

    def __setitem__(self, key, value):
        self._localNS[key] = value

    def __delitem__(self, key):
        del self._localNS[key]

    def __len__(self):
        return len(self._localNS)

    def __iter__(self):
        for ns in self._localNS:
            yield ns

    def __contains__(self, key):
        return key in self._localNS

    def __repr__(self, repr=repr):
        return repr(self._localNS)
    
    def __str__(self):
        return pprint.pformat(self._localNS, indent=4, depth=2, width=10)

    def __getattr__(self, name):
        if name in ["_localNS", "_parent_"]:
            raise AttributeError()
        if name in self._localNS:
            return self._localNS[name]
        if self._parent:
            return self._parent[name]
        raise AttributeError()

    def __setattr__(self, name, value):
        if name in ["_localNS", "_parent_"]:
            raise AttributeError("Read only attribute: '%s'" % name)
        if name in self.__dict__:
            self.__dict__[name] = value
            return
        self._localNS[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            del self.__dict__[name]
            return
        del self._localNS[name]
        
    def purgeNS(self):
        del self.__dict__['_localNS']
        self.__dict__['_localNS'] = {}
        
    def __del__(self):
        del self.__dict__['_parent_']
        self.purgeNS()
        
    def __hash__(self):
        return id(self)
            
def initNS(f):
    def wrapped_f(self, *args, **kwargs):
        parent = kwargs.pop("_parent", None)
        Namespace.__init__(self, parent)
        return f(self, *args, **kwargs)
    return wrapped_f

def callerNS():
    try:
        ret = inspect.currentframe().f_back.f_back.f_locals["self"]
        if not isinstance(ret,  Namespace):
            ret = None
    except:
        ret = None
    return ret

def autoNS(f):
    def wrapped_f(self, *args, **kwargs):
        parent =  callerNS()
        Namespace.__init__(self, parent)
        return f(self, *args, **kwargs)
    return wrapped_f
