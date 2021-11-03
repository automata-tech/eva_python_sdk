class Subject:
    def __init__(self):
        self.events = {}

    def register(self, event, callback):
        if event not in self.events:
            self.events[event] = set()
        self.events[event].add(callback)

    def deregister(self, event, callback):
        if event not in self.events:
            return
        if callback not in self.events[event]:
            return
        self.events[event].remove(callback)

    def notify(self, event, *args):
        if event not in self.events:
            return
        for callback in self.events[event]:
            callback(*args)
