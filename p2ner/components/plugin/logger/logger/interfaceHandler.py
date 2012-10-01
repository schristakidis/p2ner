import logging
#import sys
 
class interfaceHandler(logging.Handler):
    def __init__(self,func):
        logging.Handler.__init__(self)
        self.func=func

        
    def emit(self, record):
        try:
            self.func.logRecord(record)
        except:
            pass
            #print "Unexpected error:", sys.exc_info()