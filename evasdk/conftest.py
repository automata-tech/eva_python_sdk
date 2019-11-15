import pytest


def pytest_addoption(parser):
    parser.addoption("--ip", default='172.16.16.2', help="IP of the test robot, defaults to 172.16.16.2")
    parser.addoption("--token", default='', help="API token of the test robot")


@pytest.fixture(scope="session")
def ip(request):
    return request.config.getoption("--ip")


@pytest.fixture(scope="session")
def token(request):
    return request.config.getoption("--token")
