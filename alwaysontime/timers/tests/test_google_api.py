from unittest.mock import patch

import pytest

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


class TestEvents:
    def test_call_endpoint_with_correct_parameters(self):
        # now_plus_7_days = now + datetime.timedelta(days=7)
        # return calendar_service \
        #     .events() \
        #     .list(calendarId=settings.SHARED_CALENDAR_ID,
        #           timeMin=to_google_format(now_minus_1_hour),
        #           timeMax=to_google_format(now_plus_7_days),
        #           maxResults=100,
        #           singleEvents=True,
        #           orderBy='startTime') \
        #     .execute() \
        #     .get('items', [])
        pass

    def test_returns_the_events(self):
        # Test here that it extracts from the json response
        pass

    def test_returns_empty_list_if_no_events(self):
        # Test here that it extracts from the json response
        pass

    def test_raise_error_if_request_failed(self):
        # Not sure how to test that. We'll see
        pass
