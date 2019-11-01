from eva-sdk import Eva, EvaAutoRenewError, EvaError
import time
import pytest
import logging


@pytest.fixture(scope="module")
def eva(ip, token):
    e = Eva(ip, token, request_timeout=10, renew_period=2*60)
    e._Eva__logger.setLevel(logging.DEBUG)
    e._Eva__http_client._EvaHTTPClient__logger.setLevel(logging.DEBUG)
    yield e
    if e.lock_status()['status'] != 'unlocked':
        e.unlock()


@pytest.fixture
def locked_eva(eva):
    with eva.lock():
        yield eva


class TestAuth:
    def test_create_new_session(self, eva):
        token = eva.auth_create_session()
        assert(len(token) == 36)
        assert(token == eva._Eva__http_client.session_token)


    def test_invalidate_session(self, eva):
        # start a new session, then invalidate it
        token = eva.auth_create_session()
        eva.auth_invalidate_session()

        # this should automatically start a new, different session
        eva.users_get()
        assert(token != eva._Eva__http_client.session_token)


    def test_auto_renew_error(self, eva):
        api_token = eva._Eva__http_client.api_token
        eva._Eva__http_client.api_token = ''

        # Ensure it will try to auto-renew
        eva.auth_invalidate_session()
        time.sleep(3*60)

        got_auto_renew_error = False

        try:
            # Won't get a 401, as no session required for this endpoint
            eva.api_call_with_auth('GET', '_/init')
        except EvaAutoRenewError:
            got_auto_renew_error = True
        finally:
            eva._Eva__http_client.api_token = api_token
            assert(got_auto_renew_error)


    def test_lock_with_no_existing_session(self, eva):
        try:
            eva.auth_invalidate_session()
        except EvaError:
            # could fail if session is already invalidated, so ignore!
            pass

        with eva.lock():
            eva.gpio_set('d1', not eva.gpio_get('d1', 'output'))


    def test_auto_renew(self, locked_eva):
        for _ in range(7):
            locked_eva.gpio_set('d1', not locked_eva.gpio_get('d1', 'output'))
            time.sleep(5*60)
