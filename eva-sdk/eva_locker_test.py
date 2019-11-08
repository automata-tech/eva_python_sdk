import unittest
from unittest.mock import Mock
import time


from .eva_locker import EvaWithLocker


class MockEva():
    def lock(self):
        pass


    def lock_renew(self):
        pass


    def unlock(self):
        pass


class TestEvaWithLocker(unittest.TestCase):
 

    def setUp(self):
        self.mock = Mock(spec=MockEva)
        self.testEvaWithLocker = EvaWithLocker(self.mock, 0.01)


    def test_lock_no_renew(self):
        try:
            with self.testEvaWithLocker:
                pass
        except Exception:
            self.fail("should not raise an exception")
        
        self.mock.lock.assert_not_called()
        self.mock.unlock.assert_called_once()
        self.mock.lock_renew.assert_called_once()


    def test_lock_with_renew(self):
        try:
            with self.testEvaWithLocker:
                time.sleep(0.02)
        except Exception:
            self.fail("should not raise an exception")
        
        self.mock.lock.assert_not_called()
        self.mock.unlock.assert_called_once()
        assert self.mock.lock_renew.call_count == 2


    def test_double_lock_should_raise(self):
        with self.assertRaises(Exception):
            with self.testEvaWithLocker:
                with self.testEvaWithLocker:
                    self.fail("did not raise exception when locking an already locked Eva")
        self.mock.lock.assert_not_called()
        self.mock.unlock.assert_called_once()
        self.mock.lock_renew.assert_called_once()


    def test_not_locked_should_raise(self):
        self.mock.lock_renew.side_effect = Exception("can't renew a unlocked eva")

        with self.assertRaises(Exception):
            with self.testEvaWithLocker:
                self.fail("did not raise exception when renewing a not locked Eva")
        self.mock.lock.assert_not_called()
        self.mock.unlock.assert_not_called()
        self.mock.lock_renew.assert_called_once()


if __name__ == '__main__':
    unittest.main()
