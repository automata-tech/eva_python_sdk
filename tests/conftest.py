from evasdk import Eva
import pytest
import logging


def pytest_addoption(parser):
    parser.addoption("--ip", default='172.16.16.2', help="IP of the test robot, defaults to 172.16.16.2")
    parser.addoption("--token", default='', help="API token of the test robot")
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


@pytest.fixture(scope="session")
def ip(request):
    return request.config.getoption("--ip")


@pytest.fixture(scope="session")
def token(request):
    return request.config.getoption("--token")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="module")
def eva(ip, token):
    e = Eva(ip, token, request_timeout=10, renew_period=2 * 60)
    e._Eva__logger.setLevel(logging.DEBUG)
    e._Eva__http_client._EvaHTTPClient__logger.setLevel(logging.DEBUG)
    yield e
    if e.lock_status()['status'] != 'unlocked':
        e.unlock()


@pytest.fixture
def locked_eva(eva):
    with eva.lock():
        yield eva
