from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
import pytz

import timers.google_api
from alwaysontime.settings import GOOGLE_SCOPES
from conftest import TEST_GOOGLE_APP_CLIENT_ID, TEST_GOOGLE_APP_SECRET
from timers.google_api import GoogleCalendarApi

pytestmark = pytest.mark.django_db


@pytest.fixture
def CredentialsMock():
    with patch.object(timers.google_api, 'Credentials') as CredentialsMock:
        CredentialsMock().expired = False
        CredentialsMock.reset_mock()
        yield CredentialsMock


class TestInit:
    def test_create_credentials_from_user_token_using_google_app(
            self, CredentialsMock, test_user
    ):
        token = 'token'
        refresh_token = 'refresh_token'

        GoogleCalendarApi(token, refresh_token)

        CredentialsMock.assert_called_once_with(
                token=token,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=TEST_GOOGLE_APP_CLIENT_ID,
                client_secret=TEST_GOOGLE_APP_SECRET,
                scopes=GOOGLE_SCOPES
        )

    @patch.object(timers.google_api, 'Request')
    def test_refresh_credentials_if_expired(
            self, RequestMock, CredentialsMock, test_user
    ):
        credentials_mock = CredentialsMock()
        credentials_mock.expired = True

        GoogleCalendarApi('not_used', 'not_used')

        credentials_mock.refresh.assert_called_once_with(RequestMock())

    def test_dont_refresh_credentials_if_not_expired(
            self, CredentialsMock, test_user
    ):
        credentials_mock = CredentialsMock()
        credentials_mock.expired = False

        GoogleCalendarApi('not_used', 'not_used')

        credentials_mock.refresh.assert_not_called()

    @patch.object(timers.google_api, 'build')
    def test_build_calendar_service_with_credentials(
            self, build_mock, CredentialsMock, test_user
    ):
        credentials_mock = CredentialsMock()
        GoogleCalendarApi('not_used', 'not_used')
        build_mock.assert_called_once_with('calendar',
                                           'v3',
                                           credentials=credentials_mock)


@pytest.fixture
def build_mock():
    with patch.object(timers.google_api, 'build') as build_mock:
        yield build_mock


@pytest.fixture
def google_api(CredentialsMock, build_mock):
    return GoogleCalendarApi('not_used', 'not_used')


class TestEvents:
    def test_call_endpoint_with_correct_parameters(self,
                                                   test_user,
                                                   google_api,
                                                   build_mock):
        calendar_id = 'id'
        before__06_05_in_utc = datetime(
                2020, 4, 2, 6, 5,
                tzinfo=timezone.utc
        )
        after__16_45_in_utc_p3 = datetime(
                2020, 4, 2, 16, 45,
                tzinfo=timezone(timedelta(hours=3))
        )
        after__13_45_in_utc = datetime(
                2020, 4, 2, 13, 45,
                tzinfo=timezone.utc
        )
        # Sanity check
        assert after__13_45_in_utc == after__16_45_in_utc_p3
        order_by = 'order_by'

        google_api.events(calendar_id,
                          before__06_05_in_utc,
                          after__16_45_in_utc_p3,
                          order_by)

        service_mock = build_mock()
        service_mock.events().list.assert_called_with(
                calendarId=calendar_id,
                timeMin='2020-04-02T06:05:00Z',
                timeMax='2020-04-02T13:45:00Z',
                maxResults=100,
                singleEvents=True,
                orderBy=order_by
        )

        service_mock.events().list().execute.assert_called_once()

    def test_raises_if_called_with_naive_datetime(self,
                                                  test_user,
                                                  google_api,
                                                  build_mock):
        with pytest.raises(RuntimeError) as e:
            before__without_timezone = datetime(2020, 4, 2, 6, 5)
            after__without_timezone = datetime(2020, 4, 3, 8, 15)
            google_api.events('not_used',
                              before__without_timezone,
                              after__without_timezone,
                              'not_used')

        assert str(e.value) == \
               "Make sure to set 'tzinfo' in 'before' and 'after' parameters"

    def test_returns_the_events(self, test_user, google_api, build_mock):
        service_mock = build_mock()
        service_mock.events().list().execute.return_value = {
            'items': [{
                'id': 'event_id_1234',
                'summary': 'Some Event',
                'start': {
                    'dateTime': '2021-12-24T19:30:00Z',
                    # Timezone is returned but the 'dateTime' already contains
                    # timezone info `Z` == `UTC`. So `timeZone` must be ignored
                    'timeZone': 'America/Vancouver'},
                'end': {
                    'dateTime': '2021-12-24T20:30:00Z',
                    'timeZone': 'America/Vancouver'},
            }]
        }

        unused = None
        unused_dt = datetime.now(tz=pytz.utc)
        events = google_api.events(unused, unused_dt, unused_dt, unused)

        assert events == [
            {
                'id': 'event_id_1234',
                'name': 'Some Event',
                'start': datetime(
                        2021, 12, 24, 19, 30,
                        tzinfo=pytz.utc
                ),
                'end': datetime(
                        2021, 12, 24, 20, 30,
                        tzinfo=pytz.utc
                )
            }
        ]

    def test_returns_empty_list_if_no_events(
            self, test_user, google_api, build_mock
    ):
        service_mock = build_mock()
        service_mock.events().list().execute.return_value = {}

        unused = None
        unused_dt = datetime.now(tz=pytz.utc)
        events = google_api.events(unused, unused_dt, unused_dt, unused)

        assert events == []

    @pytest.mark.skip('TODO')
    def test_raise_error_if_request_failed(self):
        # Not sure how to test that. We'll see
        # There may be a 'HttpError' when
        # - creating the credentials
        # - building the service
        # - querying the service
        # Not sure if it can happen in all scenarios, but definitely in some
        pass


class TestCalendars:
    def test_call_endpoint_with_no_parameters(
            self, test_user, google_api, build_mock
    ):
        google_api.calendars()

        service_mock = build_mock()
        service_mock.calendarList().list.assert_called_once_with()
        service_mock.calendarList().list().execute.assert_called_once()

    def test_returns_the_calendars(self, test_user, google_api, build_mock):
        service_mock = build_mock()
        service_mock.calendarList().list().execute.return_value = {
            'items': [
                {'id': 'somecal@group.v.calendar.google.com',
                 'summary': 'Birthdays'},
                {'id': 'someothercal@group.calendar.google.com',
                 'summary': 'My Calendar'}
            ]
        }

        calendars = google_api.calendars()

        assert calendars == [
            {'id': 'somecal@group.v.calendar.google.com',
             'name': 'Birthdays'},
            {'id': 'someothercal@group.calendar.google.com',
             'name': 'My Calendar'}
        ]

    def test_returns_empty_list_if_no_calendars(
            self, test_user, google_api, build_mock
    ):
        service_mock = build_mock()
        service_mock.calendarList().list().execute.return_value = {}

        calendars = google_api.calendars()

        assert calendars == []

    @pytest.mark.skip('TODO')
    def test_raise_error_if_request_failed(self):
        # Not sure how to test that. We'll see
        # There may be a 'HttpError' when
        # - creating the credentials
        # - building the service
        # - querying the service
        # Not sure if it can happen in all scenarios, but definitely in some
        pass
