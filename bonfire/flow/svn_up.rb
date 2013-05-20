require 'rubygems'
require 'yaml'
require 'pp'
require 'restfully'
require 'restfully/addons/bonfire'


EXP_NAME = "PyExp"
MONITOR = "BonFIRE-Monitor"
PRODUCER = "p2pProducer"
CLIENT = "Client"

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
    e['name'] == EXP_NAME && e['status'] == "running"
  }
  if experiment == nil
    puts "Didnt find a Running Experiment"
    exit
  end
  monitorIP = experiment.computes[0]['context']['wan_ip']
  experiment.computes.each{ |compute|
    if compute['name'] == PRODUCER
      compute.ssh do |ssh|
        puts ssh.exec!("svn up --username sakis --password sakis4440 --non-interactive flow")
      end
    
    elsif compute['name'] == CLIENT
      compute.ssh do |ssh|
        puts ssh.exec!("svn up --username sakis --password sakis4440 --non-interactive flow")
      end
    
    end
  }
  
end

