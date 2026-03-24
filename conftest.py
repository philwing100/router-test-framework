import pytest
from lib.router_client import RouterClient

ROUTER_HOST = "192.168.1.1"
ROUTER_USER = "admin"
ROUTER_PASS = "admin"  # override with --router-password CLI arg or env var


def pytest_addoption(parser):
    parser.addoption("--router-host", default=ROUTER_HOST, help="Router IP address")
    parser.addoption("--router-user", default=ROUTER_USER, help="Router username")
    parser.addoption("--router-password", default=ROUTER_PASS, help="Router password")


@pytest.fixture(scope="session")
def router(request):
    host = request.config.getoption("--router-host")
    user = request.config.getoption("--router-user")
    password = request.config.getoption("--router-password")

    client = RouterClient(host=host, user=user, password=password)
    client.connect()
    yield client
    client.disconnect()
