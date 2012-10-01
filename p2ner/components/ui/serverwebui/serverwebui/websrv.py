# -*- coding: utf-8 -*
from p2ner.abstract.ui import UI
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Site
from twisted.web.static import File
from twisted.internet import reactor
import re, os

current_dir = os.path.dirname(__file__)

class WebUI(UI):
    def initUI(self, serverport = 8880):
        r = P2Main(self)
        reactor.listenTCP(serverport, Site(r))
        self.log.info('WebServer listening on port %s...' % str(serverport))


class P2Main(Resource):
    isLeaf = True
    def __init__(self, parent):
        Resource.__init__(self)
        self.parent = parent
        
    def render(self, request):
        ret = """<!DOCTYPE html>
<html>
<head>
<title>P2ner Server</title>
<link rel="stylesheet" type="text/css"
 href="http://ajax.googleapis.com/ajax/libs/dojo/1.7.2/dijit/themes/claro/claro.css" />
 
<link rel="stylesheet" type="text/css"
 href="http://ajax.googleapis.com/ajax/libs/dojo/1.7.2/dojox/grid/resources/Grid.css" />
 
 <link rel="stylesheet" type="text/css"
 href="http://ajax.googleapis.com/ajax/libs/dojo/1.7.2/dojox/grid/resources/claroGrid.css" />
</head>
 
<body class="claro">
    <table id="p2nerGrid" dojoType="dojox.grid.DataGrid">
        <thead>
            <tr>
                <th field="streamid">ID</th>
                <th field="description" width="200px">Description</th>
                <th field="type">Type</th>
                <th field="name">Name</th>
                <th field="author">Author</th>
                <th field="onair">On Air</th>
                <th field="peers">Watching</th>
            </tr>
        </thead>
    </table>

<script src="//ajax.googleapis.com/ajax/libs/dojo/1.7.2/dojo/dojo.js" data-dojo-config="parseOnLoad:true"></script>


<script type="text/javascript">
    dojo.require("dojox.grid.DataGrid");
    dojo.require("dojo.data.ItemFileReadStore");
</script>
 
<script type="text/javascript">
dojo.ready(function() {
    var AvailableStreams = {
        items: [ """
        for ovid in self.parent.overlays:
            ov = self.parent.overlays[ovid]
            ret = """%s {
                streamid: "%s",
                description: "%s",
                type: "%s",
                name: "%s",
                author: "%s",
                onair: "%s",
                peers: "%d"
                },
                """ % (ret, \
                       re.escape(str(ovid)), \
                       re.escape(str(ov.stream.description)), \
                       re.escape(str(ov.stream.type)), \
                       re.escape(str(ov.stream.filename)), \
                       re.escape(str(ov.stream.author)), \
                       str(ov.stream.live is True), \
                       len(ov.neighbourhoods) \
                       )
        foot = """
               ],
        identifier: "streamid"
    };
 
    var dataStore =
    new dojo.data.ItemFileReadStore(
        { data:AvailableStreams }
    );
    var grid = dijit.byId("p2nerGrid");
    grid.setStore(dataStore);
});
</script>
 
</body>
</html>"""
        ret = "".join([ret, foot])
        return ret
        
