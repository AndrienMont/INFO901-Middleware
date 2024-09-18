import threading
from Message import *

from pyeventbus3.pyeventbus3 import *


class Com(Thread):

    def __init__(self, clock, process):
        Thread.__init__(self)
        self.setName("Com")
        PyBus.Instance().register(self, self)

        self.owner = process.myId
        self.lamportClock = clock
        self.clockSemaphor = threading.Semaphore()
        self.mailBox = []

    def inc_clock(self):
        with self.clockSemaphor:
            self.lamportClock += 1

    def get_clock(self):
        with self.clockSemaphor:
            return self.lamportClock
    
    def getFirstMessage(self):
        if len(self.mailBox) > 0:
            return self.mailBox.pop(0)
        return None
    
    def addMessage(self, message : Message):
        self.mailBox.append(message)


    @subscribe(threadMode=Mode.PARALLEL, onEvent=DedicatedMessage)
    def onReceive(self, event):
        if event.destination == self.getName():
            if self.lamportClock < event.clockStamp:
                self.inc_clock()
            else:
                self.lamportClock = event.clockStamp + 1
        self.addMessage(event)
        print(self.getName() + " receives: " + event.content + " from " + event.expeditor + " at " + str(event.clockStamp))

    def sendTo(self, content, destination):
        self.inc_clock()
        PyBus.Instance().post(DedicatedMessage(exp = self.getName(), content = content, clock = self.lamportClock, dest = destination))