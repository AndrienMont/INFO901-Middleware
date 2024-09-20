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
        self.process = process
        self.lamportClock = clock
        self.clockSemaphor = threading.Semaphore()
        self.tokenLock = threading.Event()
        self.syncLock = threading.Barrier(self.process.npProcess)
        self.senderLockSync = threading.Event()
        self.receiverLockSync = threading.Event()
        self.mailBox = []

    def inc_clock(self):
        '''
        Increments the Lamport logical clock by 1 in a thread-safe manner.
        '''
        with self.clockSemaphor:
            self.lamportClock += 1

    def get_clock(self):
        '''
        Returns the lamport clock of the communicator
        '''
        with self.clockSemaphor:
            return self.lamportClock
    
    def getFirstMessage(self):
        '''
        Returns the first message in the mailbox if there is one, otherwise returns None
        '''
        if len(self.mailBox) > 0:
            return self.mailBox.pop(0)
        return None
    
    def addMessage(self, message : Message):
        self.mailBox.append(message)


    @subscribe(threadMode=Mode.PARALLEL, onEvent=DedicatedMessage)
    def onReceive(self, event):
        '''
        Receives and processes a DedicatedMessage event
        '''
        if event.dest == self.owner:
            if self.lamportClock < event.clockStamp:
                self.inc_clock()
            else:
                self.lamportClock = event.clockStamp + 1
            self.addMessage(event)
            print(str(self.owner) + " receives: " + event.content + " at " + str(event.clockStamp))

    def sendTo(self, content, destination):
        '''
        Sends a DedicatedMessage event to the specified destination
        '''
        self.inc_clock()
        PyBus.Instance().post(DedicatedMessage(exp = self.owner, content = content, clock = self.lamportClock, dest = destination))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, event):
        '''
        Receives and processes a BroadcastMessage event
        '''
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
        '''
        Broadcasts a BroadcastMessage event to all processes
        '''
        self.inc_clock()
        PyBus.Instance().post(BroadcastMessage(exp = self.owner, content = content, clock = self.lamportClock))

    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event):
        '''
        Receives and processes a Token event
        '''
        if self.owner == event.dest and self.process.alive : 
            sleep(1)
            if self.process.state == "request" :
                self.tokenLock.set()
                self.process.state == "SC"
                self.tokenLock.clear()
                self.tokenLock.wait(10)
            event.setDest((self.owner + 1) % self.process.npProcess)
            PyBus.instance().post(event)
            self.process.state = None

    def requestSC(self) : 
        '''
        Requests the critical section
        '''
        self.process.state = "request"
        self.tokenLock.clear()
        self.tokenLock.wait(10)

    def releaseSC(self) : 
        '''
        Releases the critical section
        '''
        self.process.state = "release"
        self.tokenLock.set()

    def firstTokenSend(self) : 
        '''
        Sends the first token to the next process
        '''
        destination = (self.owner + 1) % self.process.npProcess
        PyBus.Instance().post(Token(destination))

    def synchronize(self):
        '''
        Locks the processess until they're all synchronized
        '''
        self.syncLock.wait()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastSync)
    def onBroadcastSync(self, event):
        '''
        Receives and processes a BroadcastSync event
        '''
        if event.exp != self.owner : 
            if self.lamportClock > event.clockStamp:
                self.inc_clock()
            else:
                self.lamportClock = event.clockStamp + 1
            self.addMessage(event)
            self.synchronize()

    def broadcastSync(self, payload, exp):
        '''
        Broadcasts a BroadcastSync event to all processes
        '''
        if self.owner == exp :
            self.inc_clock()
            message = BroadcastSync(exp = self.owner, content = payload, clock = self.lamportClock)
            PyBus.Instance().post(message)
            self.synchronize()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncDedicatedMessage)
    def onReceiveSync(self, event):
        '''
        Receives and processes a SyncDedicatedMessage event
        '''
        if event.dest == self.owner:
            if self.lamportClock < event.clockStamp:
                self.inc_clock()
            else:
                self.lamportClock = event.clockStamp + 1
            self.addMessage(event)
            self.senderLockSync.set()

    def sendToSync(self, content, dest):
        '''
        Sends a SyncDedicatedMessage event to the specified destination
        '''
        self.inc_clock()
        PyBus.Instance().post(SyncDedicatedMessage(exp = self.owner, content = content, clock = self.lamportClock, dest = dest))
        self.senderLockSync.clear()
        self.senderLockSync.wait(10)

    def receiveSync(self, msg):
        '''
        Receives a SyncDedicatedMessage event
        '''
        self.receiverLockSync.clear()
        self.receiverLockSync.wait(10)
        if self.lamportClock < msg.clockStamp:
            self.inc_clock()
        else:
            self.lamportClock = msg.clockStamp + 1
        self.addMessage(msg)
        PyBus.Instance().post(SyncDedicatedMessage(exp = self.owner, content = "ACK", clock = self.lamportClock, dest = msg.exp))