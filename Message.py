from abc import ABC

class Message(ABC):
    def __init__(self, exp = None, content = None, clockStamp = None, dest = None):
        self.exp = exp
        self.content = content
        self.clockStamp = clockStamp
        self.dest = dest

    
class Token(Message):
    def __init__(self, dest):
        super().__init__(dest=dest)

    def setDest(self, dest):
        self.dest = dest

class DedicatedMessage(Message):
    def __init__(self, exp, content, clock, dest):
        super().__init__(exp, content, clock, dest)

class BroadcastMessage(Message):
    def __init__(self, exp, content, clock):
        super().__init__(exp, content, clock)

class BroadcastSync(Message):
    def __init__(self, exp, content, clock):
        super().__init__(exp, content, clock)

class SyncDedicatedMessage(Message):
    def __init__(self, exp, content, clock, dest):
        super().__init__(exp, content, clock, dest)