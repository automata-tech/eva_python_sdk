import threading
import re


class threadsafe_object:
    """
    threadsafe_object is an object wrapped in a mutex for threadsafe getting and setting.
    Set is a reserved keyword in python so we'll use update instead.
    """
    def __init__(self):
        self.object_lock = threading.Lock()
        self.object = None


    def update(self, obj):
        self.object_lock.acquire()
        self.object = obj
        self.object_lock.release()


    def get(self):
        self.object_lock.acquire()
        obj = self.object
        self.object_lock.release()
        return obj


def strip_ip(host_address):
    """
    strip_ip will remove http and ws prefixes from a host address
    """
    regex = re.compile(r"(https)?(http)?(ws)?://(www\.)?")
    new = regex.sub('', host_address).strip().strip('/')

    return new
