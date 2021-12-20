from unittest import TestCase

from dateutil.parser import isoparse
from django.utils.text import Truncator


class SandboxTestCase(TestCase):
    def setUp(self):
        pass

    def test_list_concat(self):
        concatlist = [1, 2, 3]
        self.assertEqual(concatlist, [1, 2, 3])

        concatlist = concatlist + [4, 5, 6]
        self.assertEqual(concatlist, [1, 2, 3, 4, 5, 6])

    def test_date_parsing(self):
        date_str = '2021-12-23T08:30:00Z'
        date = isoparse(date_str)
        self.assertEqual(date.day, 23)
        self.assertEqual(date.tzname(), 'UTC')

    def test_truncation(self):
        text = 'This is some very long text, like veeeeeery long long text'
        truncated = Truncator(text).chars(20)
        self.assertEqual(len(truncated), 20)
        self.assertEqual(truncated, 'This is some very l…')
