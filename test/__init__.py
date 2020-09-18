from unittest import TestCase


class TestStringMethods(TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')


def find_device(all_devices):
    return ""


class DeviceFinderTest(TestCase):

    def test_accept_powermate_device(self):
        all_devices = []
        device = find_device(all_devices)
        self.assertIsInstance(device, TestCase)
