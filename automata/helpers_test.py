import unittest

from .helpers import (strip_ip)

class Test_strip_ip(unittest.TestCase):

    def test_with_http(self):
        self.assertEqual(strip_ip("http://192.168.1.245"), "192.168.1.245")

    def test_with_https(self):
        self.assertEqual(strip_ip("https://192.168.1.245"), "192.168.1.245")

    def test_with_ws(self):
        self.assertEqual(strip_ip("ws://192.168.1.245"), "192.168.1.245")

    def test_with_no_prefix(self):
        self.assertEqual(strip_ip("192.168.1.245"), "192.168.1.245")

if __name__ == '__main__':
    unittest.main()
