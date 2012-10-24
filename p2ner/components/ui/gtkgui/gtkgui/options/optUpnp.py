import os, sys
#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except:
    pass
import pygtk
from twisted.internet import reactor
pygtk.require("2.0")
import gtk
import gobject
from generic import genericFrame
import p2ner.util.config as config
from pkg_resources import resource_string

class upnpFrame(genericFrame):
    def __init__(self,parent=None):
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        """
        try:
            self.builder.add_from_file(os.path.join(path, 'optUPNP.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'optUPNP.glade'))
        """
        self.builder.add_from_string(resource_string(__name__, 'optUPNP.glade'))
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('upnpFrame')
        
        try:
            check=config.config.getboolean('UPNP','on')
        except:
            check=True
            
        self.checkButton=self.builder.get_object('checkButton')
        
        self.checkButton.set_active(check)  

    def save(self):
        config.config.set('UPNP','on',self.checkButton.get_active())
