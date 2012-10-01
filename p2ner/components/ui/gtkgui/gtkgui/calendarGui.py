import os, sys
import os.path
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from datetime import date

class CalendarGui(object):
    
    def __init__(self,parent):
        self.parent=parent
        self.parametres={}
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path,'calendar.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'calendar.glade'))
            
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