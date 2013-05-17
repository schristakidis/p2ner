require 'rubygems'
require 'yaml'
require 'pp'
require 'restfully'
require 'restfully/addons/bonfire'

CONFIG_FILE = "config.yml"

conf = YAML::load( File.read(CONFIG_FILE) )
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
    e['name'] == conf['experiment']['name'] && e['status'] == "running"
  }
  
  fail 'experiment not running' if  experiment.nil?
  
  len=experiment.computes.length
  

  
  (1..len-1).each{|vm| 
	client=experiment.computes[vm]
	pp client['name']
	client.ssh do |ssh|
		puts ssh.exec!("apt-get install psmisc")
		puts ssh.exec!("killall /usr/bin/python")
	end
	}

end
