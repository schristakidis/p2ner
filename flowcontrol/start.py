import xmlrpclib



serverIP = "127.0.0.1"
serverXport = 8000
proxy = xmlrpclib.ServerProxy("http://%s:%d/" % (serverIP, serverXport), allow_none=True)
proxy.start()
