from evasdk import Eva
import pytest
import logging


def pytest_addoption(parser):
    parser.addoption("--ip", default='172.16.16.2', help="IP of the test robot, defaults to 172.16.16.2")
    parser.addoption("--token", default='', help="API token of the test robot")
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")
    parser.addoption("--runrobot", action="store_true", default=False, help="run tests that require a connected Eva")
    parser.addoption(
        "--io_loopback",
        action="store_true",
        default=False,
        help="run tests that require head and base IO loopback cables connected to Eva",
    )


@pytest.fixture(scope="session")
def ip(request):
    return request.config.getoption("--ip")


@pytest.fixture(scope="session")
def token(request):
    return request.config.getoption("--token")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "robot_required: no mocks, needs a connected Eva to run")
    config.addinivalue_line(
        "markers",
        "io_loopback_required: require head and base IO loopback cables connected to Eva",
    )


def pytest_collection_modifyitems(config, items):
    # --runslow given in cli: do not skip slow tests
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    # --runrobot given in cli: do not skip tests where a connected Eva is required
    if not config.getoption("--runrobot"):
        skip_robot_required = pytest.mark.skip(reason="need --runrobot option to run")
        for item in items:
            if "robot_required" in item.keywords:
                item.add_marker(skip_robot_required)

    # --io_loopback given in cli: do not skip tests requiring
    # attached base and ee IO loopback cables
    if not config.getoption("--io_loopback"):
        skip_io_loopback_required = pytest.mark.skip(reason="need --io_loopback option to run")
        for item in items:
            if "io_loopback_required" in item.keywords:
                item.add_marker(skip_io_loopback_required)


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
