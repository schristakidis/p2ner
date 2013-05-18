require 'rubygems'
require 'yaml'
require 'pp'
require 'restfully'
require 'restfully/addons/bonfire'


CONFIG_FILE = "config.yml"
SERVER_IMAGE_NAME = "BonFIRE Debian Squeeze v2"
WAN_NAME = "BonFIRE WAN"

logger = Logger.new(STDOUT)
logger.level = Logger::INFO
session = Restfully::Session.new(
  :configuration_file => "~/.restfully/api.bonfire-project.eu.yml",
  :gateway => "ssh.bonfire.grid5000.fr",
  :keys => ["~/.ssh/id_bonfire"],
  :cache => false,
  :logger => logger
  )

conf = YAML::load( File.read(CONFIG_FILE) )
puts "#{conf['experiment']['description']} - #{Time.now.to_s}"
experiment = nil

begin
  # Find an existing running experiment with the same name or submit a new
  # one. This allows re-using an experiment when developing a new script.
  experiment = session.root.experiments.find{|e|
    e['name'] == conf['experiment']['name'] && e['status'] == "running"
  } || session.root.experiments.submit(
    :name => conf['experiment']['name'],
    :description => "#{conf['experiment']['description']} - #{Time.now.to_s}",
    :walltime => conf['experiment']['walltime']
  )

  #start monitoring VM
  s = conf['experiment']['monitoring']['site']
  monitor_site = session.root.locations[s.to_sym]
  fail "Can't select the #{s} location for monitoring" if monitor_site.nil?
  
  session.logger.info "Launching Monitoring VM..."
  monitor = experiment.computes.find{|vm|
    vm['name'] == "BonFIRE-Monitor#{experiment['id']}"
  } || experiment.computes.submit(
    :name => "BonFIRE-monitor#{experiment['id']}",
    :instance_type => "small",
    :disk => [{
      :storage => monitor_site.storages.find{|s|
        s['name'] == conf['experiment']['monitoring']['img']
      },
      :type => "OS"
    }],
    :nic => [
      {:network => monitor_site.networks.find{|n| n['name'] == WAN_NAME}}
    ],
    :context => [
      {'aggregator_ip' => "127.0.0.1", 'usage' => "zabbix-agent;infra-monitoring-init"}
    ],
    :location => monitor_site
  )
  monitor_ip = monitor['nic'][0]['ip']
  session.logger.info "AGGREGATOR IP=#{monitor_ip}"

  # Create vizir site:
  s = conf['experiment']['vizir']['site']  
  vizir_site = session.root.locations[s.to_sym]
  fail "Can't select the #{s} location for vizir" if vizir_site.nil?

  session.logger.info "Launching Vizir VM..."
  vizir = experiment.computes.find{|vm|
    vm['name'] == "P2P-vizir#{experiment['id']}"
  } || experiment.computes.submit(
    :name => "P2P-vizir#{experiment['id']}",
    :instance_type => "small",
    :disk => [{
      :storage => vizir_site.storages.find{|s|
        s['name'] == conf['experiment']['vizir']['img']
      },
      :type => "OS"
    }],
    :nic => [
      {:network => vizir_site.networks.find{|n| n['name'] == WAN_NAME}},
      {:network => vizir_site.networks.find{|n| n['name'] == "Public Network"}}
    ],
    :context => [{
      'aggregator_ip' => monitor_ip,
      'usage'         => "zabbix-agent",
    }],
    :location => vizir_site
  )
  vizir_ip = vizir['nic'][0]['ip']
  session.logger.info "VIZIR IP=#{vizir_ip}"
  vizir_public_ip = vizir['nic'][1]['ip']
  session.logger.info "VIZIR PUBLIC IP=#{vizir_public_ip}"



  # Create clients:
  conf['experiment']['clients'].each { |client_s|
      if client_s['number'] > 0  
      s = client_s['site']
      client_site = session.root.locations[s.to_sym]
      fail "Can't select the #{s} location for client" if client_site.nil?
      img = client_s['img']
      img_storage = client_site.storages.find{|stor| stor['name'] == img}
       
      session.logger.info "Launching #{client_s['number']} client VM(s) \"#{img}\" on site #{s}..."
      end
      1.upto(client_s['number']) { |instance|
          
	  session.logger.info "# #{instance}"
          client = experiment.computes.find{|vm|
            vm['name'] == "P2P-client#{experiment['id']}-#{s}-#{instance}"
            } || experiment.computes.submit(
            :name => "P2P-client#{experiment['id']}-#{s}-#{instance}",
            :instance_type => "small",
            :disk => [{
              :storage => img_storage,
              :type => "OS"
            }],
            :nic => [
              {:network => client_site.networks.find{|n| n['name'] == client_s['net']}}
            ],
            :context => [{
	      'aggregator_ip' => monitor_ip,
	      'usage'         => "zabbix-agent",
	    }],
            :location => client_site
        )
        client_ip = client['nic'][0]['ip']
        session.logger.info "IP=#{client_ip}"
        sleep 1
        }    

      }

  experiment.update(:status => "running")
  session.logger.info "RUNNING"

  sleep conf['experiment']['walltime']
  experiment.delete

rescue Exception => e
  session.logger.error "#{e.class.name}: #{e.message}"
  session.logger.error e.backtrace.join("\n")
  session.logger.warn "Cleaning up in 10 seconds. Hit CTRL-C now to keep your VMs..."
  sleep 10
  experiment.delete unless experiment.nil?
end

