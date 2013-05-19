'''
Created on 04.03.2012

@author: kca
'''
from BrokerEntity import BasicBrokerEntity

class Quota(BasicBrokerEntity):
	__fields__ = (
		("cpu", int),
		("memory", int),
		("num_vms", int),
		("storage", int),
	)

class Account(BasicBrokerEntity):
	__fields__ = (
		("quota", Quota),
		("usage", Quota),
	)