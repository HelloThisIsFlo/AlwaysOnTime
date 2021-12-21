from unittest.mock import patch

import pytest

import timers.calendar
from alwaysontime.settings import GOOGLE_SCOPES
from conftest import TEST_GOOGLE_TOKEN, TEST_GOOGLE_REFRESH_TOKEN, \
    TEST_GOOGLE_APP_CLIENT_ID, TEST_GOOGLE_APP_SECRET
from timers.calendar import refresh_all_events

pytestmark = pytest.mark.django_db


class TestInit:
    def test_create_credentials_from_user_token(self):
        pass

    def test_refresh_credentials_if_expired(self):
        pass

    def test_dont_refresh_credentials_if_not_expired(self):
        pass

    def test_build_calendar_service_with_credentials(self):
        pass


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


## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##
## TODO: This needs to be migrated still!! ##

@pytest.mark.skip
@patch.object(timers.calendar, 'Credentials')
def test_create_credentials_from_user_token(CredentialsMock,
                                            test_user):
    CredentialsMock().expired = False
    CredentialsMock.reset_mock()

    refresh_all_events(test_user)

    CredentialsMock.assert_called_once_with(
            token=TEST_GOOGLE_TOKEN,
            refresh_token=TEST_GOOGLE_REFRESH_TOKEN,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=TEST_GOOGLE_APP_CLIENT_ID,
            client_secret=TEST_GOOGLE_APP_SECRET,
            scopes=GOOGLE_SCOPES
    )


@pytest.mark.skip
@patch.object(timers.calendar, 'Request')
@patch.object(timers.calendar, 'Credentials')
def test_refresh_credentials_if_expired(CredentialsMock,
                                        RequestMock,
                                        test_user):
    credentials_mock = CredentialsMock()
    credentials_mock.expired = True
    refresh_all_events(test_user)
    credentials_mock.refresh.assert_called_once_with(RequestMock())


@pytest.mark.skip
@patch.object(timers.calendar, 'Credentials')
def test_dont_refresh_credentials_if_not_expired(CredentialsMock,
                                                 test_user):
    credentials_mock = CredentialsMock()
    credentials_mock.expired = False
    refresh_all_events(test_user)
    credentials_mock.refresh.assert_not_called()


@pytest.mark.skip
@patch.object(timers.calendar, 'build')
@patch.object(timers.calendar, 'Credentials')
def test_build_calendar_service_with_credentials(CredentialsMock,
                                                 build_mock,
                                                 test_user):
    credentials_mock = CredentialsMock()
    credentials_mock.expired = False
    refresh_all_events(test_user)
    build_mock.assert_called_once_with('calendar',
                                       'v3',
                                       credentials=credentials_mock)
