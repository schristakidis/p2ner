require 'rubygems'
require 'yaml'
require 'pp'
require 'restfully'
require 'restfully/addons/bonfire'

CONFIG_FILE = "config.yml"

conf = YAML::load( File.read(CONFIG_FILE) )["experiment"]
logger = Logger.new(STDOUT)
logger.level = Logger::INFO
session = Restfully::Session.new(
  :configuration_file => "~/.restfully/api.bonfire-project.eu.yml",
  :gateway => "ssh.bonfire.grid5000.fr",
  :keys => ["~/.ssh/id_bonfire"],
  :cache => false,
  :logger => logger
  )



begin
  experiment = session.root.experiments.find{|e|
    e['name'] == conf['name'] && e['status'] == "running"
  }
  
  fail 'experiment not running' if  experiment.nil?
  
  zabbix = experiment.computes.find{|vm|
      vm['name'] == "BonFIRE-monitor#{experiment['id']}"
        } 
  fail 'zabbix not running' if zabbix.nil?
  
  items = []
  triggers = []
  computes = experiment.computes
  hosts = experiment.zabbix.request("host.get",
      {"output" => "extend",
       "search" => {"host" => "P2P-Client#{experiment['id']}"}
      }).each{ |host|
       puts host["host"]
         vmid = host["host"].split(pattern='-')[-1]
         vmip = computes.find{|h|
            h["id"].end_with?(vmid)
            }["nic"][0]["ip"]

         appli = experiment.zabbix.request("application.create",
           {"name" => conf["monitoring"]["application"]["name"],
           "hostid" => host["hostid"]
           }
           )["applicationids"][0]
         
         conf["monitoring"]["application"]["triggers"].each {|trigger_conf|
           #item = experiment.zabbix.request("item.create",
	   items <<
             {"description" => trigger_conf["description"],
             "key_" => trigger_conf["key"],
             "hostid" => host["hostid"],
             "applications" => [appli],
             "type" => trigger_conf["type"],
             "trapper_hosts" => "#{vmip}",
             "value_type" => trigger_conf["value_type"]
            }#)

           trigger = experiment.zabbix.request("trigger.create",
           triggers <<  {"description" => trigger_conf["description"],
             "expression" => "{#{host['host']}:#{trigger_conf["key"]}.last(0)}=0",
             "status" => 0,
             }

        }
      }
  item = experiment.zabbix.request("item.create",items)
  trigger = experiment.zabbix.request("trigger.create",triggers)
  pp "END"
end

