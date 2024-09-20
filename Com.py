import threading
from time import sleep
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
        if event.dest == self.owner:
            if self.lamportClock < event.clockStamp:
                self.inc_clock()
            else:
                self.lamportClock = event.clockStamp + 1
            self.addMessage(event)
            print(str(self.owner) + " receives: " + event.content + " at " + str(event.clockStamp))

    def sendTo(self, content, destination):
        self.inc_clock()
        PyBus.Instance().post(DedicatedMessage(exp = self.owner, content = content, clock = self.lamportClock, dest = destination))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, event):
        if event.exp != self.owner :
            sleep(1)
            if self.lamportClock > event.clockStamp:
                self.inc_clock()
            else:
                self.lamportClock = event.clockStamp + 1
            if event not in self.mailBox : 
                self.addMessage(event)
            print(str(self.owner) + " receives: " + event.content + " at " + str(event.clockStamp))
            sleep(1)

    def broadcast(self, content):
        self.inc_clock()
        PyBus.Instance().post(BroadcastMessage(exp = self.owner, content = content, clock = self.lamportClock))