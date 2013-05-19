'''
Created on 13.12.2010

@author: kca
'''

class EntityData(object):
    def __init__(self, name, location = None, xml = None, values = None, experiment = None, href = None, entity_class = None):
        self.name = name
        self.location = location
        self.xml = xml
        self.values = values
        self.href = href
        self.experiment = experiment
        self.entity_class = entity_class