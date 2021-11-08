from evasdk import Eva
import pytest
import logging


# each tuple contains (flag, mark, reason) where:
# - flag: the cli flag used to enable the tests with that mark
# - mark: the pytest mark to label a test with to enable skipping
# - reason: the description of why that mark exists
test_skip_marks = [
    ("--runslow", "slow", "are long running"),
    ("--runrobot", "robot_required", "require a connected Eva"),
    ("--io_loopback", "io_loopback_required", "require head and base IO loopback cables connected to Eva"),
]


def pytest_addoption(parser):
    parser.addoption("--ip", default='172.16.16.2', help="IP of the test robot, defaults to 172.16.16.2")
    parser.addoption("--token", default='', help="API token of the test robot")
    for (flag, _, reason) in test_skip_marks:
        parser.addoption(
            flag,
            action="store_true",
            default=False,
            help=f'run tests that {reason}',
        )


def pytest_configure(config):
    for (_, mark, reason) in test_skip_marks:
        config.addinivalue_line("markers", f'{mark}: marked tests {reason}')


def pytest_collection_modifyitems(config, items):
    for (flag, mark, _) in test_skip_marks:
        if not config.getoption(flag):
            skip_mark = pytest.mark.skip(reason=f'needs {flag} option to run')
            for item in items:
                if mark in item.keywords:
                    item.add_marker(skip_mark)


@pytest.fixture(scope="session")
def ip(request):
    return request.config.getoption("--ip")


@pytest.fixture(scope="session")
def token(request):
    return request.config.getoption("--token")


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
