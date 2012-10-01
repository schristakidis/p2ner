class interface(object):
    specs={'bufsize':30,
                 'blocksec':10,
                 'reqInt':2}
    
    specsGui={'bufsize':{'name':'Buffer Size','tooltip':'The size of the buffer in blocks. Typical values 20-40'},
                      'blocksec':{'name':'Blocks/sec','tooltip':'One second of video is divided to that number of blocks. Typical values 5-20'},
                      'reqInt':{'name':'Request Interval','tooltip':'How often the peers request new blocks as a fraction of blocks/sec. Typical Values 2-4'}}