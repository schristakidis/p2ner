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
    if compute['name'] == MONITOR
      compute.ssh do |ssh|
        ssh.exec!("iptables -t nat -F")
        ssh.exec!("iptables -t nat -A PREROUTING -p tcp -m tcp --dport 443 -j DNAT --to-destination 150.140.186.115:443")
        ssh.exec!("iptables -t nat -A POSTROUTING -j MASQUERADE")
        ssh.exec!("echo 1 > /proc/sys/net/ipv4/ip_forward")
      end
    elsif compute['name'] == PRODUCER
      compute.ssh do |ssh|
        ssh.exec!("apt-get install subversion psmisc -y")
        ssh.exec!("apt-get install iptraf iperf -y")
        puts ssh.exec!("svn co svn://#{monitorIP}:443/p2ner/trunk/p2ner/flowcontrol --username sakis --password sakis4440 --non-interactive flow")
      end
    
    elsif compute['name'].include? CLIENT
      compute.ssh do |ssh|
        ssh.exec!("apt-get install subversion psmisc -y")
        ssh.exec!("apt-get install iptraf iperf -y")
        puts ssh.exec!("svn co svn://#{monitorIP}:443/p2ner/trunk/p2ner/flowcontrol --username sakis --password sakis4440 --non-interactive flow")
      end
    
    end
  }
  
end

