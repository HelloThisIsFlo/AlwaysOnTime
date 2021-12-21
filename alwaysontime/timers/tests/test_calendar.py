from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, ANY, call

import pytest
from django.contrib.auth.models import User

import timers.calendar as calendar
from conftest import TEST_GOOGLE_TOKEN, TEST_GOOGLE_REFRESH_TOKEN, TEST_USERNAME
from timers.models import Calendar

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


def test_save_events_to_the_db():
    # TODO
    pass


def create_test_calendar(google_id, active):
    test_user = User.objects.get(username=TEST_USERNAME)
    Calendar.objects.create(
            google_id=google_id,
            name='name_' + google_id,
            user=test_user,
            active=active
    )
