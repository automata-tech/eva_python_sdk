from automata import Eva
import time
import pytest
import logging


@pytest.fixture(scope="module")
def eva():
    e = Eva('172.16.16.2', 'b2a54715-96cf-4248-bc8e-2580bb1a3e37', request_timeout=10)
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


    def test_lock_with_no_existing_session(self, eva):
        eva.auth_invalidate_session()
        with eva.lock():
            eva.gpio_set('d1', not eva.gpio_get('d1', 'output'))


    def test_auto_renew(self, locked_eva):
        for _ in range(7):
            locked_eva.gpio_set('d1', not locked_eva.gpio_get('d1', 'output'))
            time.sleep(5*60)


    def test_user_session_management(self, eva):
        # when passing in a session token, the instances session should not be changed/broken
        user_session = eva.auth_create_session(managed_session=False)
        sdk_session = eva.auth_create_session()
        assert(user_session != sdk_session)
        assert(sdk_session == eva._Eva__http_client.session_token)

        time.sleep(25*60)
        eva.auth_renew_session(token=user_session)
        eva.auth_renew_session()
        time.sleep(10*60)

        assert(sdk_session == eva._Eva__http_client.session_token)

        eva.auth_invalidate_session(token=user_session)
        eva.auth_renew_session()
        assert(sdk_session == eva._Eva__http_client.session_token)
