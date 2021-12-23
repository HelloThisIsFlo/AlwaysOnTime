from datetime import datetime, timezone, timedelta
from unittest.mock import patch, ANY, call

import pytest
from django.contrib.auth.models import User

import timers.calendar as calendar
from conftest import TEST_GOOGLE_TOKEN, TEST_GOOGLE_REFRESH_TOKEN, TEST_USERNAME
from timers.models import Calendar, Event

pytestmark = pytest.mark.django_db


@pytest.fixture
def GoogleCalendarApiMock():
    with patch.object(calendar, 'GoogleCalendarApi') as GoogleCalendarApiMock:
        yield GoogleCalendarApiMock


class TestRefreshEvents:
    def test_instantiate_google_api_with_user_tokens(
            self, GoogleCalendarApiMock, test_user
    ):
        calendar.refresh_events(test_user)
        GoogleCalendarApiMock.assert_called_once_with(
                token=TEST_GOOGLE_TOKEN,
                refresh_token=TEST_GOOGLE_REFRESH_TOKEN
        )

    def test_gets_events_for_all_active_calendars(
            self, GoogleCalendarApiMock, test_user
    ):
        api_mock = GoogleCalendarApiMock()
        create_test_calendar('cal1', active=True)
        create_test_calendar('cal2', active=False)
        create_test_calendar('cal3', active=True)

        calendar.refresh_events(test_user)

        assert api_mock.events.call_count == 2
        api_mock.events.assert_has_calls([
            call('cal1', before=ANY, after=ANY, order_by=ANY),
            call('cal3', before=ANY, after=ANY, order_by=ANY),
        ], any_order=True)

    @patch.object(calendar, 'timezone')
    def test_gets_events_in_the_right_timeframe_and_sorted_by_start_date(
            self, timezone_mock, GoogleCalendarApiMock, test_user
    ):
        api_mock = GoogleCalendarApiMock()
        now = datetime.now(tz=timezone.utc)
        timezone_mock.now.return_value = now
        create_test_calendar('cal1', active=True)

        calendar.refresh_events(test_user)

        api_mock.events.assert_called_once_with(
                'cal1',
                before=now - timedelta(hours=1),
                after=now + timedelta(days=2),
                order_by='startTime'
        )

    def test_save_events_to_the_db(
            self, GoogleCalendarApiMock, test_user
    ):
        api_mock = GoogleCalendarApiMock()
        test_cal = create_test_calendar('cal1', active=True)
        start1 = datetime(2021, 10, 15, 10, 5, tzinfo=timezone.utc)
        start2 = datetime(2021, 10, 15, 11, 5, tzinfo=timezone.utc)
        start3 = datetime(2021, 10, 15, 12, 5, tzinfo=timezone.utc)
        end1 = datetime(2021, 10, 15, 13, 5, tzinfo=timezone.utc)
        end2 = datetime(2021, 10, 15, 14, 5, tzinfo=timezone.utc)
        end3 = datetime(2021, 10, 15, 15, 5, tzinfo=timezone.utc)
        api_mock.events.return_value = [
            {'id': 'id1', 'name': 's1', 'start': start1, 'end': end1},
            {'id': 'id2', 'name': 's2', 'start': start2, 'end': end2},
            {'id': 'id3', 'name': 's3', 'start': start3, 'end': end3},
        ]

        calendar.refresh_events(test_user)

        assert Event.objects.filter(google_id='id1').exists()
        event1 = Event.objects.get(google_id='id1')
        assert event1.google_id == 'id1'
        assert event1.name == 's1'
        assert event1.start == start1
        assert event1.end == end1
        assert event1.calendar == test_cal

        assert Event.objects.filter(google_id='id2').exists()
        event2 = Event.objects.get(google_id='id2')
        assert event2.google_id == 'id2'
        assert event2.name == 's2'
        assert event2.start == start2
        assert event2.end == end2
        assert event2.calendar == test_cal

        assert Event.objects.filter(google_id='id3').exists()
        event3 = Event.objects.get(google_id='id3')
        assert event3.google_id == 'id3'
        assert event3.name == 's3'
        assert event3.start == start3
        assert event3.end == end3
        assert event3.calendar == test_cal

    def test_update_existing_events(
            self, GoogleCalendarApiMock, test_user, test_user_calendar,
            another_user, another_user_calendar
    ):
        api_mock = GoogleCalendarApiMock()
        Event.objects.create(google_id='id1',
                             name='Should updated',
                             start=datetime.now(),
                             end=datetime.now(),
                             calendar=test_user_calendar)
        Event.objects.create(google_id='id1',
                             name="Should NOT update <- Same 'google_id' "
                                     "but different 'calendar'",
                             start=datetime.now(),
                             end=datetime.now(),
                             calendar=another_user_calendar)

        start1 = datetime(year=2021, month=10, day=15, hour=10, minute=5)
        end1 = datetime(year=2021, month=10, day=15, hour=13, minute=5)
        api_mock.events.return_value = [
            {'id': 'id1', 'name': 'UPDATED', 'start': start1, 'end': end1},
        ]

        calendar.refresh_events(test_user)

        assert Event.objects.count() == 2
        assert Event.objects.get(
                google_id='id1',
                calendar__user=test_user
        ).name == 'UPDATED'
        assert Event.objects.get(
                google_id='id1',
                calendar__user=another_user
        ).name == "Should NOT update <- Same 'google_id' " \
                     "but different 'calendar'"

    def test_delete_all_events_not_returned_by_api(
            self, GoogleCalendarApiMock, test_user, another_user_calendar
    ):
        api_mock = GoogleCalendarApiMock()
        test_cal = create_test_calendar('cal1', active=True)

        Event.objects.create(google_id='id1',
                             name='Should be deleted',
                             start=datetime.now(),
                             end=datetime.now(),
                             calendar=test_cal)
        Event.objects.create(google_id='id1',
                             name='Should NOT be deleted <- different user',
                             start=datetime.now(),
                             end=datetime.now(),
                             calendar=another_user_calendar)

        start2 = datetime(year=2021, month=10, day=15, hour=11, minute=5)
        end2 = datetime(year=2021, month=10, day=15, hour=14, minute=5)
        api_mock.events.return_value = [
            {'id': 'id2', 'name': 's2', 'start': start2, 'end': end2}
        ]

        calendar.refresh_events(test_user)

        assert not Event.objects.filter(
                google_id='id1',
                calendar=test_cal
        ).exists()
        assert Event.objects.filter(
                google_id='id1',
                calendar=another_user_calendar
        ).exists()
        assert Event.objects.filter(
                google_id='id2',
                calendar=test_cal
        ).exists()


class TestCalendars:
    def test_instantiate_google_api_with_user_tokens(
            self, GoogleCalendarApiMock, test_user
    ):
        calendar.refresh_calendars(test_user)
        GoogleCalendarApiMock.assert_called_once_with(
                token=TEST_GOOGLE_TOKEN,
                refresh_token=TEST_GOOGLE_REFRESH_TOKEN
        )

    def test_gets_all_calendars(
            self, GoogleCalendarApiMock, test_user
    ):
        api_mock = GoogleCalendarApiMock()
        calendar.refresh_calendars(test_user)
        api_mock.calendars.assert_called_once_with()

    def test_save_calendars_as_inactive_to_the_db(
            self, GoogleCalendarApiMock, test_user
    ):
        api_mock = GoogleCalendarApiMock()
        api_mock.calendars.return_value = [
            {'id': 'id1', 'name': 'cal1'},
            {'id': 'id2', 'name': 'cal2'},
            {'id': 'id3', 'name': 'cal3'}
        ]

        calendar.refresh_calendars(test_user)

        assert Calendar.objects.count() == 3
        assert Calendar.objects.filter(google_id='id1').exists()
        cal1 = Calendar.objects.get(google_id='id1')
        assert cal1.google_id == 'id1'
        assert cal1.name == 'cal1'
        assert cal1.user == test_user
        assert not cal1.active

        assert Calendar.objects.filter(google_id='id2').exists()
        cal2 = Calendar.objects.get(google_id='id2')
        assert cal2.google_id == 'id2'
        assert cal2.name == 'cal2'
        assert cal2.user == test_user
        assert not cal2.active

        assert Calendar.objects.filter(google_id='id3').exists()
        cal3 = Calendar.objects.get(google_id='id3')
        assert cal3.google_id == 'id3'
        assert cal3.name == 'cal3'
        assert cal3.user == test_user
        assert not cal3.active

    def test_does_not_update_active_state_on_existing_calendars(
            self, GoogleCalendarApiMock, test_user
    ):
        Calendar.objects.create(
                google_id='id1',
                name='exists in db and is active',
                user=test_user,
                active=True
        )
        api_mock = GoogleCalendarApiMock()
        api_mock.calendars.return_value = [
            {'id': 'id1', 'name': 'exists in db and is active - UPDATE'},
            {'id': 'id2', 'name': 'cal2'}
        ]

        calendar.refresh_calendars(test_user)

        assert Calendar.objects.count() == 2
        assert Calendar.objects.filter(google_id='id1').exists()
        cal1 = Calendar.objects.get(google_id='id1')
        assert cal1.name == 'exists in db and is active - UPDATE'
        assert cal1.active

    def test_uses_google_id_and_user_to_determine_existing_calendars(
            self, GoogleCalendarApiMock, test_user, another_user
    ):
        Calendar.objects.create(
                google_id='shared_google_id',
                name='To update',
                user=test_user,
                active=True
        )
        Calendar.objects.create(
                google_id='shared_google_id',
                name='DO NOT UPDATE <-- Different user',
                user=another_user,
                active=True
        )
        api_mock = GoogleCalendarApiMock()
        api_mock.calendars.return_value = [
            {'id': 'shared_google_id', 'name': 'UPDATED'}
        ]

        calendar.refresh_calendars(test_user)

        assert Calendar.objects.count() == 2
        assert Calendar.objects.get(
                google_id='shared_google_id',
                user=test_user
        ).name == 'UPDATED'
        assert Calendar.objects.get(
                google_id='shared_google_id',
                user=another_user
        ).name == 'DO NOT UPDATE <-- Different user'

    def test_marks_calendars_not_returned_by_api_as_inactive(
            self, GoogleCalendarApiMock, test_user, another_user
    ):
        Calendar.objects.create(google_id='id1',
                                name='active',
                                user=test_user,
                                active=True)
        Calendar.objects.create(google_id='id2',
                                name='active => will be set to inactive',
                                user=test_user,
                                active=True)
        Calendar.objects.create(google_id='id2',
                                name='keep active'
                                     ' <- another user, same google_id',
                                user=another_user,
                                active=True)
        api_mock = GoogleCalendarApiMock()
        api_mock.calendars.return_value = [
            {'id': 'id1', 'name': 'still active'}
            # calendar 'id2' is not returned by the api
        ]

        calendar.refresh_calendars(test_user)

        assert Calendar.objects.filter(google_id='id2').exists()
        assert not Calendar.objects.get(
                google_id='id2',
                user=test_user
        ).active
        assert Calendar.objects.get(
                google_id='id2',
                user=another_user
        ).active


def create_test_calendar(google_id, active):
    test_user = User.objects.get(username=TEST_USERNAME)
    return Calendar.objects.create(
            google_id=google_id,
            name='name_' + google_id,
            user=test_user,
            active=active
    )
