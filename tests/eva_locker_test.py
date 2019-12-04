import unittest
from unittest.mock import Mock
import time


from evasdk.eva_locker import EvaWithLocker


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
        self.mock.lock_renew.assert_called_once()
        self.mock.unlock.assert_called_once()


    def test_lock_with_renew(self):
        try:
            with self.testEvaWithLocker:
                time.sleep(0.015)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 2)
        self.mock.unlock.assert_called_once()


    def test_not_locked_should_raise(self):
        self.mock.lock_renew.side_effect = Exception("can't renew an unlocked eva")

        with self.assertRaises(Exception):
            with self.testEvaWithLocker:
                self.fail("did not raise exception when renewing a not locked Eva")

        self.mock.lock.assert_not_called()
        self.mock.lock_renew.assert_called_once()
        self.mock.unlock.assert_not_called()


    def test_nested_locker_same_period_should_raise(self):
        with self.assertRaises(Exception):
            with self.testEvaWithLocker:
                with self.testEvaWithLocker:
                    self.fail("did not raise exception when locking an already locked Eva")

        self.mock.lock.assert_not_called()
        self.mock.lock_renew.assert_called_once()
        self.mock.unlock.assert_called_once()


    def test_nested_locker_entry_and_exit_renews_lock(self):
        try:
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(1):
                    pass
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 3)
        self.mock.unlock.assert_called_once()


    def test_nested_locker_different_period_with_inner_renew(self):
        try:
            with self.testEvaWithLocker:
                time.sleep(0.005)
                with self.testEvaWithLocker.set_renew_period(0.05):
                    time.sleep(0.09)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 4)
        self.mock.unlock.assert_called_once()


    def test_nested_locker_different_period_with_outer_renew(self):
        try:
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(0.1):
                    time.sleep(0.01)
                time.sleep(0.015)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 4)
        self.mock.unlock.assert_called_once()


    def test_nested_locker_reset_on_outer_exit(self):
        try:
            # 3 renews from this context
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(0.1):
                    pass

            with self.testEvaWithLocker:
                # Sleep duration < 0.1s should still cause a renew
                time.sleep(0.015)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 5)
        self.assertEqual(self.mock.unlock.call_count, 2)


    def test_deeply_nested_contexts(self):
        try:
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(0.3):
                    with self.testEvaWithLocker.set_renew_period(0.45):
                        with self.testEvaWithLocker.set_renew_period(0.075):
                            # Sleep duration should cause a renew here
                            time.sleep(0.078)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 8)
        self.mock.unlock.assert_called_once()


    def test_locker_has_default_period(self):
        self.testEvaWithLocker = EvaWithLocker(self.mock)

        try:
            with self.testEvaWithLocker:
                # To avoid long tests: Sleep duration shorter than
                # the relatively long default should not cause a renew here
                time.sleep(0.5)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 1)
        self.mock.unlock.assert_called_once()


    def test_can_set_period_to_default(self):
        try:
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(1):
                    with self.testEvaWithLocker.set_renew_period():
                        # Sleep duration should cause a renew here
                        time.sleep(0.011)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 6)
        self.mock.unlock.assert_called_once()


    def test_nested_locker_uses_last_set_period(self):
        try:
            with self.testEvaWithLocker:
                self.testEvaWithLocker.set_renew_period(0.02)
                with self.testEvaWithLocker.set_renew_period(0.1):
                    # Sleep duration should not cause a renew here
                    time.sleep(0.05)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 3)
        self.mock.unlock.assert_called_once()


    def test_nested_locker_returns_to_parent_period(self):
        try:
            with self.testEvaWithLocker:
                # Each sleep duration should cause a single renew here
                with self.testEvaWithLocker.set_renew_period(0.1):
                    time.sleep(0.11)
                time.sleep(0.011)
        except Exception:
            self.fail("should not raise an exception")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 5)
        self.mock.unlock.assert_called_once()


    def test_handles_nested_renew_failure_on_enter(self):
        self.mock.lock_renew.side_effect = [None, Exception("Lock could not be renewed")]

        with self.assertRaises(Exception):
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(0.1):
                    self.fail("did not raise exception when renewing a not locked Eva")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 2)
        # Should have final unlock
        self.mock.unlock.assert_called_once()


    def test_handles_nested_renew_failure_on_exit(self):
        self.mock.lock_renew.side_effect = [None, None, Exception("Lock could not be renewed")]

        with self.assertRaises(Exception):
            with self.testEvaWithLocker:
                with self.testEvaWithLocker.set_renew_period(0.1):
                    pass
                self.fail("did not raise exception when renewing a not locked Eva")

        self.mock.lock.assert_not_called()
        self.assertEqual(self.mock.lock_renew.call_count, 3)
        # Should have final unlock
        self.mock.unlock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
