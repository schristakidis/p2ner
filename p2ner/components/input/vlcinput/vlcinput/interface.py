class interface(object):
    specs={'videoRate':0,'audio':'pulse','width':360,'height':240}
    
    specsGui={'videoRate':{'name':'Video Rate','tooltip':'The quality of the transcoded video in KBps. 0 for default quality'},
                      'audio':{'name':'Audio Input','tooltip':'Audio Input device. Only for camera input on linux'},
                      'width':{'name':'Width','tooltip':'The width of the encoded video'},
                      'height':{'name':'Height','tooltip':'The height of the encoded video'}}

                      