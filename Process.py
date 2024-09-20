from threading import Lock, Thread

from time import sleep

#from geeteventbus.subscriber import subscriber
#from geeteventbus.eventbus import eventbus
#from geeteventbus.event import event

from Com import Com

from pyeventbus3.pyeventbus3 import *


class Process(Thread):
        
    nbProcessCreated = 0
    def __init__(self, name, npProcess):
        Thread.__init__(self)

        self.npProcess = npProcess
        self.myId = Process.nbProcessCreated
        Process.nbProcessCreated +=1
        self.myProcessName = name
        self.setName("MainThread-" + name)
        self.communicator = Com(0, self)
        self.tokenState = None

        PyBus.Instance().register(self, self)

        self.alive = True
        self.start()
        

    def run(self):
        while self.alive:
            ##### DEDICATED MESSAGE TEST #####
            # if self.myId == self.npProcess - 1:
            #     self.communicator.sendTo("Hello", 0)
            # elif self.myId == 0 :
            #     sleep(1)
            #     message = self.communicator.getFirstMessage().content
            #     if message:
            #         print(f"Process 0 received: " + message)
            ##### BROADCAST TEST #####
            if self.myId == self.npProcess - 1:
                self.communicator.broadcast("Hey")
            else:
                sleep(1)
                message = self.communicator.getFirstMessage()
                if message and message.content:
                    print(f"Process {self.myId} received: " + message.content)
            self.stop()

    def stop(self):
        self.alive = False

    def waitStopped(self):
        self.join()

