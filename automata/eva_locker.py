import threading
import time

from .eva_errors import EvaLockError


class EvaWithLocker:
    """
    The EvaWithLocker class is used to keep an Eva locked for the entirety of a Python with scope.
    It expects an already locked Eva object to be passed in, and for the duration of the
    with scope it will renew the lock every <renew_period> seconds. At the end of the scope
    it will release the lock.
    """
    def __init__(self, eva, renew_period = 30):
        self.__eva = eva
        self.__renew_period = renew_period
        self.__locked = False
        self.__thread = None
        self.__cond = None


    def __enter__(self):
        if self.__locked:
            raise EvaLockError('Eva already locked in another "with" statement scope')

        try:
            self.__eva.lock_renew()
        except Exception:
            raise EvaLockError('"with eva:" statement requires a locked eva object, try "with eva.lock():"')

        self.__locked = True
        self.__cond = threading.Condition()
        self.__thread = threading.Thread(target=self.__start_loop)
        self.__thread.start()


    def __exit__(self, type, value, traceback):
        with self.__cond:
            self.__locked = False
            self.__cond.notify_all()
        self.__thread.join()


    def __start_loop(self):
        while True:
            with self.__cond:
                self.__cond.wait(timeout=self.__renew_period)
            if self.__locked: 
                self.__eva.lock_renew()
            else:
                self.__eva.unlock()
                return
