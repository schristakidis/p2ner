import time
from configobj import ConfigObj
from ZabbixSender.ZabbixSender import ZabbixSender
import random

config = ConfigObj('/etc/zabbix/zabbix_agentd.conf')
server = config.get('Server')
host = config.get('Hostname')

sender = ZabbixSender(server.encode('utf-8'))
for i in range(200):
    now = time.time()
    sender.AddData(host = host.encode('utf-8'), key = u'p2ner.neighno', value = i, clock = now)
    time.sleep(0.5)
    

ret = sender.Send()
print ret
sender.ClearData()
### apt-get install python-simplejson
### apt-get install python-configobj

