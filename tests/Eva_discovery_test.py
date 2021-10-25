import pytest
import time
from evasdk import find_first_eva, find_eva, find_evas, discover_evas


timeout = 1.5  # second


@pytest.mark.robot_required
class TestEva_Discovery:
    def test_find_first(self):
        assert(find_first_eva(timeout=timeout) is not None)

    def test_find_named(self):
        eva = find_first_eva(timeout=timeout)
        assert(find_eva(eva.name, timeout=timeout) is not None)

    def test_cannot_find_named(self):
        assert(find_eva("Awesome London Charlie", timeout=timeout) is None)

    def test_find_multiple(self):
        evas = find_evas(timeout=timeout)
        assert(len(evas.keys()) > 0)

    def test_context(self):
        events = []
        with discover_evas(lambda event, eva: events.append((event, eva))):
            time.sleep(timeout)
        assert(len(events) > 0)
        assert(events[0][0] == "added")
        assert(events[0][1] is not None)

    def test_connecting(self, token):
        eva = find_first_eva(timeout=timeout)
        assert(eva is not None)
        actual_eva = eva.connect(token)
        assert(actual_eva.lock_status()["owner"] is not None)
