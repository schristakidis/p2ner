from twisted.internet import reactor,defer
from twisted.web.xmlrpc import Proxy
from cPickle import loads,dumps

STREAMID=0
PORT=0

def contentsSuccess(stream):
    print 'contents'
    global STREAMID
    for s in stream:
         print s
         STREAMID=s[0]
    print STREAMID

def contentsFailed(*args):
    print 'failed'
    print args

def subSuccess(*args):
    print 'subscription success'
    print args

def subFailure(*args):
    print 'subscription failure'
    print args

def stopSuccess(*args):
    print 'subscription success'
    print args

def stopFailure(*args):
    print 'subscription failure'
    print args

def getContents(p2nerIp='127.0.0.1',p2nerPort=9090):
    url='http://'+p2nerIp+':'+str(p2nerPort)
    proxy=Proxy(url)
    d=proxy.callRemote('contactSteerServer')
    d.addCallback(contentsSuccess)
    d.addErrback(contentsFailed)


def subscribeStream(id,output,p2nerIp='127.0.0.1',p2nerPort=9090):
    #output
    #0:NullOutput
    #1:GstOutput
    #2:VlcOutput
    url='http://'+p2nerIp+':'+str(p2nerPort)
    proxy=Proxy(url)
    d=proxy.callRemote('subscribeSteerStream',STREAMID,output)
    d.addCallback(subSuccess)
    d.addErrback(subFailure)

def stopStream(id,p2nerIp='127.0.0.1',p2nerPort=9090):
    url='http://'+p2nerIp+':'+str(p2nerPort)
    proxy=Proxy(url)
    d=proxy.callRemote('unregisterStream',STREAMID)
    d.addCallback(stopSuccess)
    d.addErrback(stopFailure)

if __name__=='__main__':
    import sys
    # global PORT
    PORT=sys.argv[1]
    print PORT
    getContents(p2nerPort=PORT)
    reactor.callLater(2,subscribeStream,STREAMID,1,p2nerPort=PORT)
    # reactor.callLater(15,stopStream,STREAMID,p2nerPort=PORT)
    reactor.run()

