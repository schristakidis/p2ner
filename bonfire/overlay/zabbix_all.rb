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
COLORS = {"10" => "009900",
          "50" => "0000CC",
          "90" => "DD00DD",
          "avg" => "DD0000"}
DRAWTYPE = {"10" => "0",
            "50" => "0",
            "90" => "0",
            "avg" => "2"}

line = ""

begin
  experiment = session.root.experiments.find{|e|
    e['name'] == conf['name'] && e['status'] == "running"
  }
  
  while experiment.nil?
     session.logger.info "Experiment is not running yet"
     sleep 10
     experiment = session.root.experiments.find{|e|
         e['name'] == conf['name'] && e['status'] == "running"
     }
  end
  
  zabbix = experiment.computes.find{|vm|
      vm['name'] == "BonFIRE-monitor#{experiment['id']}"
        } 
  
  while zabbix.nil?
     session.logger.info "Zabbix is not ready. Waiting..."
     sleep 10
     zabbix = experiment.computes.find{|vm|
        vm['name'] == "BonFIRE-monitor#{experiment['id']}"
        }
  end

  until ['RUNNING', 'ACTIVE','up'].include?(zabbix.reload['state']) && zabbix.ssh.accessible?
    
    session.logger.info "Zabbix is not ready. Waiting..."
    sleep 5
  end

  zabbix = experiment.computes.find{|vm|
      vm['name'] == "BonFIRE-monitor#{experiment['id']}"
        } 
  fail 'zabbix not running' if zabbix.nil?
  
  ###
  # CLIENTS
  ###
  items = []
  computes = experiment.computes
  clientsnum = 0
  conf['clients'].each { |client_s|
        clientsnum += client_s['number'].to_i()
  }

  if ARGV.length > 1 
    clientsnum -= ARGV[1]
  end

  hosts = experiment.zabbix.request("host.get",
      {"output" => "extend",
       "search" => {"host" => "P2P-Client#{experiment['id']}"}
      })
  
  until hosts.length == clientsnum
     session.logger.info "Waiting for #{clientsnum-hosts.length} client(s) to be up..."
    sleep 15
     hosts = experiment.zabbix.request("host.get",
        {"output" => "extend",
         "search" => {"host" => "P2P-Client#{experiment['id']}"}
    })
  end
      
  hosts.each{ |host|
          session.logger.info "Setting trappers for host: \"#{host["host"]}\""
           #vmid = host["host"].split(pattern='-')[-1]
           #vmip = computes.find{|h|
           #   h["id"].end_with?(vmid)
           #   }["nic"][0]["ip"]

           appli = experiment.zabbix.request("application.create",
             {"name" => conf["monitoring"]["application"]["name"],
             "hostid" => host["hostid"]
             }
             )["applicationids"][0]
         
           conf["monitoring"]["application"]["trappers"].each {|trapper_conf|
           items <<
             {"description" => trapper_conf["description"],
             "key_" => trapper_conf["key"],
             "hostid" => host["hostid"],
             "applications" => [appli],
             "type" => trapper_conf["type"],
             #"trapper_hosts" => "#{vmip}",
             "value_type" => trapper_conf["value_type"]
             }

            }
          session.logger.info "Finish setting trappers for host: \"#{host["host"]}\""
      }
      
  session.logger.info " Finish setting trappers "
  #pp items

  #item = experiment.zabbix.request("item.create",item)
  items.each_slice(5) { |itemslice|
    ret = experiment.zabbix.request("item.create",itemislice)

  }

  session.logger.info " Staring percentile "
  ###
  # PERCENTILE
  ###
  host = experiment.zabbix.request("host.get",
      {"output" => "extend",       
       "search" => {"host" => "BonFIRE-Monitor#{experiment['id']}"}
      })[0]

  session.logger.info "Zabbix host: \"#{host["host"]}\""
  hostid = host["hostid"]
  appli = experiment.zabbix.request("application.create",
      {"name" => conf["monitoring"]["application"]["name"],
       "hostid" => hostid
      }
      )["applicationids"][0]

  session.logger.info "Application created"
  conf["monitoring"]["application"]["trappers"].each {|trapper_conf|
        if trapper_conf["percentile"]
          session.logger.info "Setting percentile trappers for \"#{trapper_conf["description"]}\""
          line = line << trapper_conf["key"] << " "
          itemids = []
          gitems = []
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

        itemids << item["itemids"][0]

          }

        itemids.each_with_index {|v, i|
            p = PERCENTILE[i]
            gitems << {"type" => "0",
                     "sortorder" => i.to_s(),
                     "periods_cnt" => "5",
                     "calc_fnc" => "2",
                     "drawtype"=> DRAWTYPE[p],
                     "color" => COLORS[p],
                     "yaxisside" => "0",
                     "itemid" => v
                    }
    
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

          p = "avg"
          gitems << {"type" => "0",
                     "sortorder" => itemids.length.to_s(),
                     "periods_cnt" => "5",
                     "calc_fnc" => "2",
                     "drawtype"=> DRAWTYPE[p],
                     "color" => COLORS[p],
                     "yaxisside" => "0",
                     "itemid" => item["itemids"][0]
                    }

        session.logger.info "Creating graph for \"#{trapper_conf["description"]}\""
        graph = experiment.zabbix.request("graph.create",
              {"gitems" => gitems,
               "name" => "#{trapper_conf["description"]} percentiles",
               "width" => "900",
               "height" => "400",
               "show_legend"=>"0",
               "show_work_period"=>"1",
               "graphtype"=>"0",
               "show_3d" => "0",
               "ymin_type" => "0",
               "ymax_type" => "0",
               "ymin_itemid" => "0",
               "ymax_itemid" => "0"
            })
        end
      
  }
  

  if line.length >0
     perc = PERCENTILE*","
     session.logger.info "Uploading patches to aggregator"
     zabbix.ssh do |ssh|
       ssh.scp.upload!("./zabbix-percentile.py", '/root/zabbix-percentile.py')
       ssh.scp.upload!("./history.php", "/usr/share/zabbix/history.php")
       ssh.scp.upload!("./gtlc.js", "/usr/share/zabbix/js/gtlc.js")
       ssh.scp.upload!("./defines.inc.php", "/usr/share/zabbix/include/defines.inc.php")
       ssh.scp.upload!("./lastlog.php", "/usr/share/zabbix/l.php")
       ssh.exec!("apt-get install python-mysqldb python-configobj python-simplejson unzip ; \
                  wget https://github.com/BlueSkyDetector/code-snippet/archive/master.zip ; \
                  unzip ./master.zip ; \
                  mv ./code-snippet-master/ZabbixSender/ZabbixSender.py . ; \
                  touch ./__init__.py ")
       session.logger.info "Starting percentile script - READY"
       puts ssh.exec!("python ./zabbix-percentile.py #{perc} #{line}")
     end
  end
  pp "END"
end
