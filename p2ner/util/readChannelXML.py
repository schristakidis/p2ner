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

import xml.dom.minidom

def getText(nodelist):
    nodelist=nodelist.childNodes
    rc=[]
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


def readChannels(file):
    try:
        dom = xml.dom.minidom.parse(file)
    except:
        return None
    channels={}
    for ch in dom.getElementsByTagName('track'):
        nm=getText(ch.getElementsByTagName('title')[0]).split()[1:]
        name=''
        for n in nm:
            name +=str(n)
        loc=getText(ch.getElementsByTagName('location')[0])
        ext=ch.getElementsByTagName('extension')[0]
        prog=getText(ext.getElementsByTagName('vlc:option')[0]).split('=')[1]
        channels[name]={}
        channels[name]['location']=str(loc)
        channels[name]['program']=int(prog)

    return channels
    