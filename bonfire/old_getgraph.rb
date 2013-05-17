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
  
  ala = experiment.zabbix.request("graph.get",{"output" => "extend", "graphids" => [386]})
  pp ala
  ala = experiment.zabbix.request("graphitem.get",{"output" => "extend", "graphids" => [386]})
  pp ala

  exit

end

