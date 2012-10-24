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

import os.path
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from datetime import date
from pkg_resources import resource_string

class CalendarGui(object):
    
    def __init__(self,parent):
        self.parent=parent
        self.parametres={}
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        """
        try:
            self.builder.add_from_file(os.path.join(path,'calendar.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'calendar.glade'))
        """
        self.builder.add_from_string(resource_string(__name__, 'calendar.glade'))
        self.builder.connect_signals(self)
        
        self.ui=self.builder.get_object('ui')
        cal=self.builder.get_object('calendar')
        d=date.today()
        cal.select_month(d.month-1,d.year)
        cal.select_day(d.day)
        self.ui.show()
        
        
    def on_okButton_clicked(self,widget):
        date=self.builder.get_object('calendar').get_date()
        self.parent.setDate(date)
        self.ui.destroy()
        
    def on_cancelButton_clicked(self,widget):
        self.ui.destroy()