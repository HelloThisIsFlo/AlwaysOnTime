from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, ANY, call

import pytest
from django.contrib.auth.models import User

import timers.calendar as calendar
from conftest import TEST_GOOGLE_TOKEN, TEST_GOOGLE_REFRESH_TOKEN, TEST_USERNAME
from timers.models import Calendar, Event

pytestmark = pytest.mark.django_db


def sandbox():
    MagicMock().assert_called_with()
    MagicMock().call_count


@patch.object(calendar, 'GoogleCalendarApi')
def test_instantiate_google_api_with_user_tokens(GoogleCalendarApiMock,
                                                 test_user):
    calendar.refresh_all_events(test_user)
    GoogleCalendarApiMock.assert_called_once_with(
            token=TEST_GOOGLE_TOKEN,
            refresh_token=TEST_GOOGLE_REFRESH_TOKEN
    )


@patch.object(calendar, 'GoogleCalendarApi')
def test_gets_events_for_all_active_calendars(GoogleCalendarApiMock, test_user):
    api_mock = GoogleCalendarApiMock()
    create_test_calendar('cal1', active=True)
    create_test_calendar('cal2', active=False)
    create_test_calendar('cal3', active=True)

    calendar.refresh_all_events(test_user)

    assert api_mock.events.call_count == 2
    api_mock.events.assert_has_calls([
        call('cal1', before=ANY, after=ANY, order_by=ANY),
        call('cal3', before=ANY, after=ANY, order_by=ANY),
    ], any_order=True)


@patch.object(calendar, 'timezone')
@patch.object(calendar, 'GoogleCalendarApi')
def test_gets_events_in_the_right_timeframe_and_sorted_by_start_date(
        GoogleCalendarApiMock, timezone_mock, test_user
):
    api_mock = GoogleCalendarApiMock()
    now = datetime.now(tz=timezone.utc)
    timezone_mock.now.return_value = now
    create_test_calendar('cal1', active=True)

    calendar.refresh_all_events(test_user)

    api_mock.events.assert_called_once_with(
            'cal1',
            before=now - timedelta(hours=1),
            after=now + timedelta(days=2),
            order_by='startTime'
    )


@patch.object(calendar, 'GoogleCalendarApi')
def test_save_events_to_the_db(
        GoogleCalendarApiMock, test_user
):
    api_mock = GoogleCalendarApiMock()
    test_cal = create_test_calendar('cal1', active=True)
    start1 = datetime(year=2021, month=10, day=15, hour=10, minute=5)
    start2 = datetime(year=2021, month=10, day=15, hour=11, minute=5)
    start3 = datetime(year=2021, month=10, day=15, hour=12, minute=5)
    end1 = datetime(year=2021, month=10, day=15, hour=13, minute=5)
    end2 = datetime(year=2021, month=10, day=15, hour=14, minute=5)
    end3 = datetime(year=2021, month=10, day=15, hour=15, minute=5)
    api_mock.events.return_value = [
        {'id': 'id1', 'summary': 's1', 'start': start1, 'end': end1},
        {'id': 'id2', 'summary': 's2', 'start': start2, 'end': end2},
        {'id': 'id3', 'summary': 's3', 'start': start3, 'end': end3},
    ]

    calendar.refresh_all_events(test_user)

    assert Event.objects.filter(google_id='id1').exists()
    assert Event.objects.get(google_id='id1') == Event(google_id='id1',
                                                       summary='s1',
                                                       start=start1,
                                                       end=end1,
                                                       calendar=test_cal)
    assert Event.objects.filter(google_id='id2').exists()
    assert Event.objects.get(google_id='id2') == Event(google_id='id2',
                                                       summary='s2',
                                                       start=start2,
                                                       end=end2,
                                                       calendar=test_cal)
    assert Event.objects.filter(google_id='id3').exists()
    assert Event.objects.get(google_id='id3') == Event(google_id='id3',
                                                       summary='s3',
                                                       start=start3,
                                                       end=end3,
                                                       calendar=test_cal)


@patch.object(calendar, 'GoogleCalendarApi')
def test_update_existing_events(
        GoogleCalendarApiMock, test_user
):
    api_mock = GoogleCalendarApiMock()
    test_cal = create_test_calendar('cal1', active=True)
    Event.objects.create(google_id='id1',
                         summary='EMPTY',
                         start=datetime.now(),
                         end=datetime.now(),
                         calendar=test_cal)

    start1 = datetime(year=2021, month=10, day=15, hour=10, minute=5)
    end1 = datetime(year=2021, month=10, day=15, hour=13, minute=5)
    api_mock.events.return_value = [
        {'id': 'id1', 'summary': 's1', 'start': start1, 'end': end1},
    ]

    calendar.refresh_all_events(test_user)

    assert Event.objects.count() == 1
    assert Event.objects.get(google_id='id1').summary == 's1'


@patch.object(calendar, 'GoogleCalendarApi')
def test_delete_all_events_not_returned_by_api(
        GoogleCalendarApiMock, test_user
):
    api_mock = GoogleCalendarApiMock()
    test_cal = create_test_calendar('cal1', active=True)

    Event.objects.create(google_id='id1',
                         summary='Should be deleted',
                         start=datetime.now(),
                         end=datetime.now(),
                         calendar=test_cal)

    start2 = datetime(year=2021, month=10, day=15, hour=11, minute=5)
    end2 = datetime(year=2021, month=10, day=15, hour=14, minute=5)
    api_mock.events.return_value = [
        {'id': 'id2', 'summary': 's2', 'start': start2, 'end': end2}
    ]

    calendar.refresh_all_events(test_user)

    assert not Event.objects.filter(google_id='id1').exists()
    assert Event.objects.filter(google_id='id2').exists()


def create_test_calendar(google_id, active):
    test_user = User.objects.get(username=TEST_USERNAME)
    return Calendar.objects.create(
            google_id=google_id,
            name='name_' + google_id,
            user=test_user,
            active=active
    )
