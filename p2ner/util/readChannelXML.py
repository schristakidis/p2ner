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
    