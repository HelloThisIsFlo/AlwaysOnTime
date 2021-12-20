from dateutil.parser import isoparse
from django.utils.text import Truncator


def test_list_concat():
    concatlist = [1, 2, 3]
    assert concatlist == [1, 2, 3]

    concatlist = concatlist + [4, 5, 6]
    assert concatlist == [1, 2, 3, 4, 5, 6]


def test_date_parsing():
    date_str = '2021-12-23T08:30:00Z'
    date = isoparse(date_str)
    assert date.day == 23
    assert date.tzname() == 'UTC'


def test_truncation():
    text = 'This is some very long text, like veeeeeery long long text'
    truncated = Truncator(text).chars(20)
    assert len(truncated) == 20
    assert truncated == 'This is some very l…'
