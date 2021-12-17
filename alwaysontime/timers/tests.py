# Create your tests here.

from dateutil.parser import isoparse
from django.test import TestCase


class SandboxTestCase(TestCase):
    def setUp(self):
        pass

    def test_list_concat(self):
        concatlist = [1, 2, 3]
        self.assertEqual(concatlist, [1, 2, 3])

        concatlist = concatlist + [4, 5, 6]
        self.assertEqual(concatlist, [1, 2, 3, 4, 5, 6])

    def test_list_concat(self):
        date_str = '2021-12-23T08:30:00Z'
        date = isoparse(date_str)
        self.assertEqual('highlight', date)
