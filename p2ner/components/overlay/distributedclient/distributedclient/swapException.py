class SwapError(Exception):
    def __init__(self, msg, peer= None,swapid=None,state=None,swapSnapshot=None):
        self.partner = peer
        self.swapid=swapid
        self.state=state
        self.swapSnapshot=swapSnapshot
        self.message=msg

    def __str__(self):
        return str(self.message)
