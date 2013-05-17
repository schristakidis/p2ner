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
  


def ssh_func(cmd,serv)
	pp cmd
	serv.ssh do |ssh|
		puts ssh.exec!("killall /usr/bin/python")
		puts ssh.exec!("svn cleanup p2ner")
		puts ssh.exec!("svn up p2ner")
		puts ssh.exec!(cmd)
	end
end  

def ssh_hp(cmd,serv,vizirIP)
	pp cmd
	serv.ssh do |ssh|
		puts ssh.exec!("killall /usr/bin/python")
		puts ssh.exec!("svn cleanup p2ner")
		puts ssh.exec!("svn switch --relocate svn://nam.ece.upatras.gr/p2ner/trunk/p2ner svn://#{vizirIP}:443/p2ner/trunk/p2ner --username sakis --password sakis4440 --non-interactive p2ner")
		puts ssh.exec!("svn up  --username sakis --password sakis4440 --non-interactive p2ner")
		puts ssh.exec!(cmd)
	end
end  

begin

  experiment = session.root.experiments.find{|e|
    e['name'] == conf['experiment']['name'] && e['status'] == "running"
  }
  
  fail 'experiment not running' if  experiment.nil?
  vizir = experiment.computes[1]
  vizir.ssh do |ssh|
    puts ssh.exec!("iptables -t nat -F")
    puts ssh.exec!("iptables -t nat -A PREROUTING -p tcp -m tcp --dport 443 -j DNAT --to-destination 150.140.186.115:443")
    puts ssh.exec!("iptables -t nat -A POSTROUTING -j MASQUERADE")
    puts ssh.exec!("echo 1 > /proc/sys/net/ipv4/ip_forward")
  end
  vizirIP=vizir['context']['wan_ip']
  vizirGui='150.140.186.118'
  len=experiment.computes.length
  
  ###start vizir
  cmd="vizirProxy -p 80 -v #{vizirGui} -P 443  &"
  t1=Thread.new{ssh_func(cmd,vizir)}
  
  ###start server
  serv=experiment.computes[2]
  cmd="p2nerServer -v #{vizirIP} -P 80  &"
  t1=Thread.new{ssh_func(cmd,serv)}
  
  ###start clients
  cmd="p2nerClient -b -v #{vizirIP} -P 80 -s &"
  pp cmd
  a=[]
  (3..len-1).each{|i| a.push(i)}
  a=a.shuffle
  
  a.each{|vm| 
	client=experiment.computes[vm]
	pp client['name']
	if client['name'].include? "uk-hplabs"
	    puts "HP"
	    t1 = Thread.new{ssh_hp(cmd,client,vizirIP)}
	else
	    t1=Thread.new{ssh_func(cmd,client)}
	end
	}
	
	pp 'finishhhhhhhhhh'
	sleep 3600000
	
end
