from typing import Callable
from dataclasses import dataclass
from threading import Condition
from .Eva import Eva
from zeroconf import ServiceBrowser, Zeroconf


CHOREO_SERVICE = "_automata-eva._tcp.local."


@dataclass
class DiscoveredEva:
    name: str
    host: str

    def connect(self, token) -> Eva:
        return Eva(self.host, token)


DiscoverCallback = Callable[[str, DiscoveredEva], None]


class EvaDiscoverer:


    def __init__(self, callback: DiscoverCallback, name: str = None):
        self.name = name
        self.callback = callback
        self.zeroconf = None

    def __enter__(self):
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, CHOREO_SERVICE, self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.zeroconf.close()

    def __get_eva(self, zeroconf: Zeroconf, service_type: str, service_name: str):
        info = zeroconf.get_service_info(service_type, service_name)
        if info is None:
            return None
        return DiscoveredEva(host=info.server, name=info.properties[b'name'].decode("utf-8"))

    def __filter_name(self, eva):
        return self.name is not None and self.name != eva.name

    def add_service(self, zeroconf: Zeroconf, service_type: str, service_name: str):
        eva = self.__get_eva(zeroconf, service_type, service_name)
        if eva is None or self.__filter_name(eva):
            return
        self.callback('added', eva)

    def remove_service(self, zeroconf: Zeroconf, service_type: str, service_name: str):
        eva = self.__get_eva(zeroconf, service_type, service_name)
        if eva is None or self.__filter_name(eva):
            return
        self.callback('removed', eva)


def __find_evas(callback: DiscoverCallback, timeout: float, name: str = None, condition: Condition = None):
    if condition is None:
        condition = Condition()
    with EvaDiscoverer(name=name, callback=callback):
        with condition:
            condition.wait(timeout=timeout)


def find_evas(timeout: float = 5):
    """Blocks for `timeout` seconds and returns a dictionary of DiscoveredEva (with their names as key) discovered in that time"""
    evas = {}

    def __callback(event: str, eva: DiscoveredEva):
        if event == 'added':
            evas[eva.name] = eva
        elif event == 'deleted':
            del evas[eva.name]

    __find_evas(callback=__callback, timeout=timeout)
    return evas


def find_eva(name: str, timeout: float = 5):
    """Blocks for a maximum of `timeout` seconds and returns a DiscoveredEva if a robot named `name` was found, or `None`"""
    eva = None
    cv = Condition()

    def __callback(event: str, eva_found: DiscoveredEva):
        nonlocal eva
        if event == 'added':
            eva = eva_found
            with cv:
                cv.notify()

    __find_evas(name=name, callback=__callback, timeout=timeout, condition=cv)
    return eva


def find_first_eva(timeout: float = 5):
    """Blocks for a maximum of `timeout` seconds and returns a DiscoveredEva if one was found, or `None`"""
    eva = None
    cv = Condition()

    def __callback(event: str, eva_found: DiscoveredEva):
        nonlocal eva
        if event == 'added' and eva is None:
            eva = eva_found
            with cv:
                cv.notify()

    __find_evas(callback=__callback, timeout=timeout, condition=cv)
    return eva


def discover_evas(callback: DiscoverCallback):
    """Returns a context that will discovers robots until exited

    It will call `callback` with 2 arguments: the event (either `added` or `removed`) and a Discovered Eva object

    Note that `callback` will be called from another thread so you will need to ensure any data accessed there is done in a thread-safe manner
    """
    return EvaDiscoverer(callback=callback)
