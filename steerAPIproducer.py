from twisted.internet import reactor,defer
from twisted.web.xmlrpc import Proxy
from cPickle import loads,dumps

STREAMID=0
PORT=0

def registationSuccess(stream):
    print 'success'
    print stream
    STREAMID=stream

def registrationFailed(*args):
    print 'failed'
    print args

def stopSuccess(*args):
    print 'stop succesful'
    print args

def stopFailure(*args):
    print 'stop failure'
    print args

def registerStream(title,author,desc,port,p2nerIp='127.0.0.1',p2nerPort=PORT):
    url='http://'+p2nerIp+':'+str(p2nerPort)
    proxy=Proxy(url)
    d=proxy.callRemote('registerSteerStream',title,author,desc,port)
    d.addCallback(registationSuccess)
    d.addErrback(registrationFailed)


def stopProducingStream(streamId,p2nerIp='127.0.0.1',p2nerPort=PORT):
    print 'should stop producing ',STREAMID
    url='http://'+p2nerIp+':'+str(p2nerPort)
    proxy=Proxy(url)
    d=proxy.callRemote('stopProducing',STREAMID)
    d.addCallback(stopSuccess)
    d.addErrback(stopFailure)

if __name__=='__main__':
    import sys
    # global PORT
    PORT=sys.argv[1]
    title='test'
    author='sakis'
    desc='test stream'
    port=5004
    registerStream(title,author,desc,port,p2nerPort=PORT)
    # reactor.callLater(20,stopProducingStream,STREAMID)
    reactor.run()

