from . import Formatter, Field
from ResourceTool import ResourceTool
from argparser_types import location_id
from bonfire_cli.exc import CLIError

class PhysicalRouterFormatter(Formatter):
    __fields__ = [
        #Field("name"),
        #Field("description"),
        Field("interfaces", "Interface")
    ]
    
    # return a list of interfaces
    def get_interfaces(self, o):
        return [ "%s (connected to %s / %s)" % (i.name, i.connected_to.host, i.connected_to.physical_interface) for i in o.interface ]
        

class BFPhysicalRouterTool(ResourceTool):
    _entity_type = "federica_physical_router"
    
    available_actions = ("show", "list")

    def _get_arg_parser(self, action, parser):
        if action == "show":
            super(BFPhysicalRouterTool, self)._get_arg_parser(action, parser)
        else:
            parser.add_argument("-L", "--location", type = location_id, default = "/locations/federica", help = "Location to search")

    def _action_list(self, args):
        return self.broker.get_federica_physical_routers(location = args.location)

    def _action_show(self, args):
        for r in self._action_list(args):
            if r.id == args.id:
                return r
            
        raise CLIError("Physical Router not found: %s" % (args.id, ))
    
    def _get_formatter(self, entity, args):
        return PhysicalRouterFormatter()
