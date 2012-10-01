import os, sys
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
import p2ner.util.config as config
from generic import genericFrame


class componentsFrame(genericFrame):
    def __init__(self,parent):
        self.components=parent.components
        
        path = os.path.realpath(os.path.dirname(sys.argv[0])) 
        self.builder = gtk.Builder()
        try:
            self.builder.add_from_file(os.path.join(path, 'optComponents.glade'))
        except:
            path = os.path.dirname( os.path.realpath( __file__ ) )
            self.builder.add_from_file(os.path.join(path, 'optComponents.glade'))
        
        self.builder.connect_signals(self)
        
        self.frame=self.builder.get_object('componentsFrame')
        self.constructComponents()
        
    def getFrame(self):
        return self.frame
        
    def constructComponents(self):
        
        for comp in ['input','output','scheduler','overlay']:
            button=self.builder.get_object(('d'+comp+'Button'))
            button.set_name(('d'+comp+'Button'))
            
            box=self.builder.get_object(('d'+comp+'Combo'))
            self.components[comp]['dcombo'] = gtk.combo_box_new_text()
            self.components[comp]['dcombo'].set_property('width-request',140)
            box.pack_start(self.components[comp]['dcombo'] ,True,True,0)
            box.show()
            self.components[comp]['dcombo'].show()
            
            default=None
            found=-1
            if config.config.has_option('Components',comp):
                default=config.config.get('Components',comp)
                
            i=0
            for sc,v in self.components[comp].items():
                if sc!='dcombo':
                    try:
                        platform=v.platform
                    except:
                        platform=None
                    if not platform or platform in sys.platform:
                        self.components[comp]['dcombo'].append_text(sc)
                        if default==sc:
                            found=i
                        i+=1
            if found>-1:
                self.components[comp]['dcombo'].set_active(found)

    def on_cdefaultButton_clicked(self,widget):
        name=widget.get_name()
        name=name[1:-6]
        default=self.get_active_text(self.components[name]['dcombo'])
        if default:
            config.config.set('Components',name,default)
        
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]
    
    def getComponents(self,component):
        ret={}
        try:
            ret['default']=config.config.get('Components',component)
        except:
            ret['default']=None
        
        model=self.components[component]['dcombo'].get_model()
        ret['comps']=[model[i][0] for i in range(len(model))]
        return ret
    