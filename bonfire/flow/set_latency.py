
from bonfire.broker import Broker
from bonfire.broker import VirtualWallNetworkResource
from bonfire.broker.occi import toprettyxml
        
USER = "schristakidis"
PASSWORD = "sakis4440"
URI = "https://api.bonfire-project.eu"
#LATENCY = "10"
import sys
LATENCY = sys.argv[1]
BANDWIDTH = sys.argv[2] 

brokerargs = {'username': USER,
              'password': PASSWORD,
              'url': "https://api.bonfire-project.eu"}
              
broker = Broker(**brokerargs)

experiment = broker.get_experiments()[0]
#net1 = broker.get_networks(location = "/locations/be-ibbt", experiment = experiment)[1]
net1 = "/locations/be-ibbt/networks/1287"
newres = VirtualWallNetworkResource("producer", "/locations/be-ibbt", experiment)
newres.latency = LATENCY
newres.bandwidth = BANDWIDTH
broker.occi("PUT", str(net1), toprettyxml(newres), validate = False)

