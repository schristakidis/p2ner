import sys, time, socket
import MySQLdb as mysql
from configobj import ConfigObj
from ZabbixSender import ZabbixSender
INTERVAL = 2

if len(sys.argv) < 2:
  print "NO KEYS GIVEN"
  sys.exit(0)

config = ConfigObj('/etc/zabbix/zabbix_server.conf')
DBHost = config.get('DBHost')
DBName = config.get('DBName')
DBUser = config.get('DBUser')
DBPassword = config.get('DBPassword')

sender = ZabbixSender(u"127.0.0.1")
senderhost = socket.gethostname().encode('utf-8')

db = mysql.connect(DBHost, DBUser, DBPassword, DBName)

percentile = map(int,sys.argv[1].split(","))
type_columns = ["history", "history_str", "history_log", "history_uint", "history_text"]
itemids = {}
itemtype = {}
for key in sys.argv[2:]:
  itemids[key] = []
  with db:
    curr = db.cursor()
    query = 'SELECT itemid,value_type from items WHERE key_="%s"'%(key);
    curr.execute(query)
    ret = curr.fetchall()
  for v in ret:
    itemids[key].append(v[0])
  itemtype[key] = type_columns[ret[0][1]]

#print itemids
#print itemtype

while(1):
  now = time.time()
  for key in itemids:
      vals = []
      for itemid in itemids[key]:
        with db:
          curr = db.cursor()
          query = "SELECT value from %s WHERE itemid=%d order by clock desc LIMIT 1"%(itemtype[key], int(itemid))
          curr.execute(query)
          ret = curr.fetchall()
          if len(ret):
            vals.append(ret[0][0])
      l = len(vals)
      if l:
        vals.sort()
        for perc in percentile:
          idx = int(round(l*perc/100))
          if idx>l-1:
            idx=l-1
          ret = float(vals[idx])
          #print key,perc,ret
          trapkey = "%s%dpercentile"%(key, perc)
          sender.AddData(host = senderhost, key = trapkey.encode('utf-8'), value = ret, clock = now)
        mean = sum(vals)/l
        trapkey = "%saverage"%(key)
        sender.AddData(host = senderhost, key = trapkey.encode('utf-8'), value = mean, clock = now)
      else:
        pass
        #print "ZEROVALUES"
  ret = sender.Send()
  #print ret
  sender.ClearData()
  time.sleep(INTERVAL)
