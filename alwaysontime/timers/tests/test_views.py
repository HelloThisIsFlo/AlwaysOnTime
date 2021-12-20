# Create your tests here.
from datetime import timedelta
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
from django.contrib.auth.models import User
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed, \
    assertContains

from timers.models import Event

TEST_PASSWORD = 'testuser1234@'
TEST_USERNAME = 'testuser'
TEST_GOOGLE_TOKEN = 'abcdefg123456'

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user_without_google_credentials():
    return User.objects.create_user(
            username=TEST_USERNAME,
            email='testuser@gmail.com',
            password=TEST_PASSWORD
    )


@pytest.fixture
def test_user(test_user_without_google_credentials):
    test_user = test_user_without_google_credentials
    SocialToken.objects.create(
            account=SocialAccount.objects.create(
                    user=test_user),
            app=SocialApp.objects.create(),
            token=TEST_GOOGLE_TOKEN,
    )
    return test_user


@pytest.fixture
def logged_in_test_user(test_user, client):
    client.login(
            username=TEST_USERNAME,
            password=TEST_PASSWORD
    )
    return test_user


class TestHomePage:
    class TestFailureScenario:
        def test_redirects_if_user_not_logged_in(self, client):
            response = client.get('/')
            assertRedirects(response, '/accounts/login/?next=/')

        def test_redirects_if_user_does_not_have_google_linked(
                self, test_user_without_google_credentials, client
        ):
            client.login(username=TEST_USERNAME,
                         password=TEST_PASSWORD)
            response = client.get('/')
            assertRedirects(response, '/accounts/social/connections/')

        def test_show_error_if_user_didnt_give_necessary_permissions(self):
            # TODO
            pass

    class TestSuccessScenario:
        def test_shows_home_page(self, logged_in_test_user, client):
            response = client.get('/')
            assertTemplateUsed(response, 'index.html')

        def test_return_next_event_in_time_as_main_event_and_rest_as_other_events(
                self, client, logged_in_test_user
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  summary='Starts in 4 hours',
                  start=timezone.now() + timedelta(hours=4),
                  end=not_used).save()
            Event(google_id='2',
                  summary='Starts in 1 minutes: This is the next one in time',
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()
            Event(google_id='3',
                  summary='Starts in 2 hours',
                  start=timezone.now() + timedelta(hours=2),
                  end=not_used).save()

            response = client.get('/')

            assert 'main_event' in response.context
            assert response.context['main_event'].summary == \
                   'Starts in 1 minutes: This is the next one in time'

            assert 'other_events' in response.context
            other_events = response.context['other_events']
            assert len(other_events) == 2
            assert other_events[0].summary == 'Starts in 2 hours'
            assert other_events[1].summary == 'Starts in 4 hours'

        def test_return_only_main_event_if_no_other_events(
                self, client, logged_in_test_user
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  summary='Starts in 1 minutes: This is the next one in time',
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()

            response = client.get('/')

            assert 'main_event' in response.context
            assert response.context['main_event'] is not None

            assert 'other_events' in response.context
            assert len(response.context['other_events']) == 0

        def test_return_none_if_no_events_at_all(
                self, client, logged_in_test_user
        ):
            response = client.get('/')

            assert 'main_event' in response.context
            assert response.context['main_event'] is None

            assert 'other_events' in response.context
            assert len(response.context['other_events']) == 0


class TestRefreshEvents:
    def test_returns_error_if_user_not_logged_in(self, client):
        response = client.post('/events/refresh/')
        assertContains(response,
                       "Please log in before refreshing!",
                       status_code=401)

    @patch('timers.views.refresh_all_events')
    def test_refreshes_the_events_of_logged_in_user(
            self, refresh_all_events_mock, logged_in_test_user, client
    ):
        response = client.post('/events/refresh/')

        assertContains(response, "Ok", status_code=200)
        refresh_all_events_mock.assert_called_with(logged_in_test_user)
