def validateIp(ip):
    fields=ip.split('.')
    if len(fields)!=4:
        return False
    
    for i in fields:
        try:
            num=int(i)
        except:
            return False
        if num<0 or num>255:
            return False
    return True
    
def validatePort(port):
    try:
        port=int(port)
    except:
        return False
    if port:
        return True
    else:
        return False