
import iso8601, time, os
from datetime import timedelta

from bonfire.broker import Broker
from bonfire.broker import Experiment, ComputeResource, Disk, Nic, DynamicReference, VirtualWallNetworkResource, DefaultNetworkResource

from bonfire.broker.occi import toprettyxml
from bonfire_cli import Formatter, Field
        
USER = "schristakidis"
PASSWORD = "sakis4440"
URI = "https://api.bonfire-project.eu"

NAME = "PyExp"
DESCRIPTION = "Test experiment"
WALLTIME = 24*60*60

brokerargs = {'username': USER,
              'password': PASSWORD,
              'url': "https://api.bonfire-project.eu"}
              
broker = Broker(**brokerargs)

exp = Experiment(NAME)
exp.groups = "p2pclouds"
exp.description = DESCRIPTION
exp.walltime = WALLTIME
experiment = broker.occi("POST", "/experiments", toprettyxml(exp), validate = False)

#Start Monitor
STORAGE = "/locations/fr-inria/storages/2592"
NETWORKS = ["/locations/fr-inria/networks/53", "/locations/fr-inria/networks/27"]
newres = ComputeResource(name = "BonFIRE-Monitor", location = "/locations/fr-inria", experiment = experiment)
newres.instance_type = "small"
newres.disk = [ Disk(STORAGE) ]
newres.disk[0].type = "OS"
newres.disk[0].target = "hda"
newres.nic = map(Nic, NETWORKS)
newres.set_context("aggregator_ip", "127.0.0.1")
newres.set_context("usage", "zabbix-agent;infra-monitoring-init")
monitor = broker.occi("POST", experiment + "/computes", toprettyxml(newres), validate = False)
monitor_ip = broker.get_entity("compute", monitor).wan_ip

#Create networks
newres = VirtualWallNetworkResource("net1", "/locations/be-ibbt", experiment)
newres.address = "192.168.0.0"
newres.size = "C"
newres.latency = "2"
newres.lossrate = "0"
newres.bandwidth = "100"
newres.groups = "p2pclouds"
producer = broker.occi("POST", experiment + "/networks", toprettyxml(newres), validate = False)

newres = VirtualWallNetworkResource("net1", "/locations/be-ibbt", experiment)
newres.address = "192.168.1.0"
newres.size = "C"
newres.latency = "2"
newres.lossrate = "0"
newres.bandwidth = "100"
newres.groups = "p2pclouds"
cl1 = broker.occi("POST", experiment + "/networks", toprettyxml(newres), validate = False)

newres = VirtualWallNetworkResource("net1", "/locations/be-ibbt", experiment)
newres.address = "192.168.2.0"
newres.size = "C"
newres.latency = "2"
newres.lossrate = "0"
newres.bandwidth = "100"
newres.groups = "p2pclouds"
cl2 = broker.occi("POST", experiment + "/networks", toprettyxml(newres), validate = False)

newres = VirtualWallNetworkResource("net1", "/locations/be-ibbt", experiment)
newres.address = "192.168.3.0"
newres.size = "C"
newres.latency = "2"
newres.lossrate = "0"
newres.bandwidth = "100"
newres.groups = "p2pclouds"
cl3 = broker.occi("POST", experiment + "/networks", toprettyxml(newres), validate = False)


'''
newres = VirtualWallNetworkResource("net2", "/locations/be-ibbt", experiment)
newres.address = "192.168.0.0"
newres.size = "C"
newres.latency = "2"
newres.lossrate = "0"
newres.bandwidth = "100"
newres.groups = "p2pclouds"
net2 = broker.occi("POST", experiment + "/networks", toprettyxml(newres), validate = False)
'''

#Start Producer
STORAGE = "/locations/be-ibbt/storages/1"
NETWORKS = ["/locations/be-ibbt/networks/1", producer]
newres = ComputeResource(name = "p2pProducer", location = "/locations/be-ibbt", experiment = experiment)
newres.instance_type = "Large-EN"
newres.disk = [ Disk(STORAGE) ]
newres.disk[0].type = "OS"
newres.disk[0].target = "hda"
newres.nic = map(Nic, NETWORKS)
newres.set_context("aggregator_ip", monitor_ip)
newres.set_context("usage", "zabbix-agent")
producer = broker.occi("POST", experiment + "/computes", toprettyxml(newres), validate = False)

#Start router
STORAGE = "/locations/be-ibbt/storages/1"
NETWORKS = ["/locations/be-ibbt/networks/1", producer, cl1, cl2, cl3]
newres = ComputeResource(name = "Router", location = "/locations/be-ibbt", experiment = experiment)
newres.instance_type = "Large-EN"
newres.disk = [ Disk(STORAGE) ]
newres.disk[0].type = "OS"
newres.disk[0].target = "hda"
newres.nic = map(Nic, NETWORKS)
newres.set_context("aggregator_ip", monitor_ip)
newres.set_context("usage", "zabbix-agent")


#Start Client
STORAGE = "/locations/be-ibbt/storages/1"
NETWORKS = ["/locations/be-ibbt/networks/1", cl1]
newres = ComputeResource(name = "Client1", location = "/locations/be-ibbt", experiment = experiment)
newres.instance_type = "Large-EN"
newres.disk = [ Disk(STORAGE) ]
newres.disk[0].type = "OS"
newres.disk[0].target = "hda"
newres.nic = map(Nic, NETWORKS)
newres.set_context("aggregator_ip", monitor_ip)
newres.set_context("usage", "zabbix-agent")
client = broker.occi("POST", experiment + "/computes", toprettyxml(newres), validate = False)

STORAGE = "/locations/be-ibbt/storages/1"
NETWORKS = ["/locations/be-ibbt/networks/1", cl2]
newres = ComputeResource(name = "Client2", location = "/locations/be-ibbt", experiment = experiment)
newres.instance_type = "Large-EN"
newres.disk = [ Disk(STORAGE) ]
newres.disk[0].type = "OS"
newres.disk[0].target = "hda"
newres.nic = map(Nic, NETWORKS)
newres.set_context("aggregator_ip", monitor_ip)
newres.set_context("usage", "zabbix-agent")
client = broker.occi("POST", experiment + "/computes", toprettyxml(newres), validate = False)

STORAGE = "/locations/be-ibbt/storages/1"
NETWORKS = ["/locations/be-ibbt/networks/1", cl2]
newres = ComputeResource(name = "Client2", location = "/locations/be-ibbt", experiment = experiment)
newres.instance_type = "Large-EN"
newres.disk = [ Disk(STORAGE) ]
newres.disk[0].type = "OS"
newres.disk[0].target = "hda"
newres.nic = map(Nic, NETWORKS)
newres.set_context("aggregator_ip", monitor_ip)
newres.set_context("usage", "zabbix-agent")
client = broker.occi("POST", experiment + "/computes", toprettyxml(newres), validate = False)


'''
while True:
    #ret = ComputeResource.test_wan_ports([broker.get_entity("compute", monitor), broker.get_entity("compute", producer), broker.get_entity("compute", client)], 22, timeout = 1000.0)
    ret = ComputeResource.test_wan_ports([broker.get_entity("compute", monitor)], 22, timeout = 5.0)
    br = True
    print ret
    for res in ret:
        if bool(ret[res]) == False:
            br = False
    if br:
        break
print "UP"


e = Experiment("dummy")
e.status = "running"
broker.occi("PUT", experiment, toprettyxml(e, ("status",)), validate = False)

newres = VirtualWallNetworkResource("net1", "/locations/be-ibbt", experiment)
newres.latency = "20"
print broker.occi("PUT", net1, toprettyxml(newres), validate = False)
'''
e = Experiment("dummy")
e.status = "running"
broker.occi("PUT", experiment, toprettyxml(e, ("status",)), validate = False)

