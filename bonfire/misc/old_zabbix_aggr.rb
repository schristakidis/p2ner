require 'rubygems'
require 'yaml'
require 'pp'
require 'restfully'
require 'restfully/addons/bonfire'

CONFIG_FILE = "./config.yml"

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



PERCENTILE = ["10", "50", "90"]
line = ""

begin
  experiment = session.root.experiments.find{|e|
    e['name'] == conf['name'] && e['status'] == "running"
  }
  
  fail 'experiment not running' if  experiment.nil?
  
  zabbix = experiment.computes.find{|vm|
      vm['name'] == "BonFIRE-monitor#{experiment['id']}"
        } 
  fail 'zabbix not running' if zabbix.nil?

  until ['RUNNING', 'ACTIVE'].include?(zabbix.reload['state']) && zabbix.ssh.accessible?
    
    session.logger.info "One of the VMs is not ready. Waiting..."
    sleep 10
  end

  host = experiment.zabbix.request("host.get",
      {"output" => "extend",       
       "search" => {"host" => "BonFIRE-Monitor#{experiment['id']}"}
      })[0]

  hostid = host["hostid"]
  appli = experiment.zabbix.request("application.create",
      {"name" => conf["monitoring"]["application"]["name"],
       "hostid" => hostid
      }
      )["applicationids"][0]

  conf["monitoring"]["application"]["trappers"].each {|trapper_conf|
        if trapper_conf["percentile"]
          line = line << trapper_conf["key"] << " "
          PERCENTILE.each {|perc_val|
           kval = "#{trapper_conf["key"]}#{perc_val}percentile"
           item = experiment.zabbix.request("item.create",
             {"description" => "#{trapper_conf["description"]} #{perc_val}th percentile",
              "key_" => kval,
              "hostid" => hostid,
              "applications" => [appli],
              "type" => trapper_conf["type"],
              "trapper_hosts" => "127.0.0.1",
              "value_type" => 0
            })

          }

          kval = "#{trapper_conf["key"]}average"
          item = experiment.zabbix.request("item.create",
             {"description" => "#{trapper_conf["description"]} average",
              "key_" => kval,
              "hostid" => hostid,
              "applications" => [appli],
              "type" => trapper_conf["type"],
              "trapper_hosts" => "127.0.0.1",
              "value_type" => 0
            })

        end
      
  }

  if line.length >0
     perc = PERCENTILE*","
     zabbix.ssh do |ssh|
       ssh.scp.upload!("./zabbix-percentile.py", '/root/zabbix-percentile.py')
       ssh.scp.upload!("./history.php", "/usr/share/zabbix/history.php")
       ssh.scp.upload!("./gtlc.js", "/usr/share/zabbix/js/gtlc.js")
       ssh.scp.upload!("./defines.inc.php", "/usr/share/zabbix/include/defines.inc.php")
       puts ssh.exec!("apt-get install python-mysqldb python-configobj python-simplejson unzip ; \
                  wget https://github.com/BlueSkyDetector/code-snippet/archive/master.zip ; \
                  unzip ./master.zip ; \
                  mv ./code-snippet-master/ZabbixSender/ZabbixSender.py . ; \
                  touch ./__init__.py ")
       puts "Starting percentile script"
       puts ssh.exec!("python ./zabbix-percentile.py #{perc} #{line}")
     end
  end
  pp "END"
end

