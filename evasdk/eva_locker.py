import threading

from .eva_errors import EvaLockError

# TODO improve timing accuracy by taking into account lock_renew() API call duration in the __renewal_timer() loop
# TODO properly handle exceptions thrown in the renewal thread
# TODO properly handle unlock on program exit


class EvaWithLocker:
    """
    The EvaWithLocker class is used to keep an Eva locked for the entirety of a Python 'with' scope.
    It expects an already locked Eva object to be passed in, and for the duration of the
    with scope it will renew the lock every <renew_period> seconds.

    'with' scopes can be nested, with the lock being renewed in a particular
    scope for the currently set 'renew_period' of the locker. At the end of the outer-most scope
    it will release the lock.
    """


    def __init__(self, eva, fallback_renew_period=30):
        self.__eva = eva
        self.__fallback_renew_period = fallback_renew_period
        self.__renew_period = fallback_renew_period
        self.__period_stack = []
        self.__thread = None
        self.__cond = None


    def set_renew_period(self, renew_period=None):
        if renew_period is None:
            self.__renew_period = self.__fallback_renew_period
        else:
            self.__renew_period = renew_period
        return self


    def __enter__(self):
        if len(self.__period_stack) == 0:
            self.__try_renew()

            self.__cond = threading.Condition()
            self.__thread = threading.Thread(target=self.__renewal_timer)

            self.__period_stack.append(self.__renew_period)
            self.__thread.start()
        else:
            with self.__cond:
                if self.__renew_period != self.__period_stack[-1]:
                    self.__try_renew()

                    self.__period_stack.append(self.__renew_period)
                    self.__reset_timer()
                else:
                    raise EvaLockError("""Unneccesary refresh of the lock renewal process,
                 lock is already being renewed with the configured period.""")


    def __exit__(self, type, value, traceback):
        context_end_size = None

        with self.__cond:
            self.__period_stack.pop()
            self.__reset_timer()

            context_end_size = len(self.__period_stack)
            if context_end_size != 0:
                self.__try_renew()

        if context_end_size == 0:
            self.__thread.join()
            self.set_renew_period()


    def __renewal_timer(self):
        with self.__cond:
            while True:
                if not self.__cond.wait(timeout=self.__period_stack[-1]):
                    # timeout has occurred: renewing
                    self.__eva.lock_renew()

                if len(self.__period_stack) == 0:
                    self.__eva.unlock()
                    return


    def __try_renew(self):
        try:
            self.__eva.lock_renew()
        except Exception:
            raise EvaLockError("""'with eva:' context statements require a locked eva object, e.g. by using 'with eva.lock():',
             and not unlocking from within the statement.""")


    def __reset_timer(self):
        self.__cond.notify()
