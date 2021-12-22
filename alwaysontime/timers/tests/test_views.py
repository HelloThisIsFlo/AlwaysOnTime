# Create your tests here.
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed, \
    assertContains

import conftest
import timers.views
from timers.models import Event, Calendar

pytestmark = pytest.mark.django_db


class TestHomePage:
    class TestFailureScenario:
        def test_redirects_if_user_not_logged_in(self, client):
            response = client.get('/')
            assertRedirects(response, '/accounts/login/?next=/')

        def test_redirects_if_user_does_not_have_google_linked(
                self, test_user_without_google_credentials, client
        ):
            client.login(username=conftest.TEST_USERNAME,
                         password=conftest.TEST_PASSWORD)
            response = client.get('/')
            assertRedirects(response, '/accounts/social/connections/')

        @pytest.mark.skip("TODO")
        def test_show_error_if_user_didnt_give_necessary_permissions(self):
            # Not sure how to test => Investigate
            pass

    class TestSuccessScenario:
        def test_shows_home_page(self, logged_in_test_user, client):
            response = client.get('/')
            assertTemplateUsed(response, 'index.html')

        def test_return_next_event_in_time_as_main_event_and_rest_as_other_events(
                self, client, logged_in_test_user, test_calendar
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  summary='Starts in 4 hours',
                  calendar=test_calendar,
                  start=timezone.now() + timedelta(hours=4),
                  end=not_used).save()
            Event(google_id='2',
                  summary='Starts in 1 minutes: This is the next one in time',
                  calendar=test_calendar,
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()
            Event(google_id='3',
                  summary='Starts in 2 hours',
                  calendar=test_calendar,
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
                self, client, logged_in_test_user, test_calendar
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  summary='Starts in 1 minutes: This is the next one in time',
                  calendar=test_calendar,
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

        def test_return_only_events_for_the_currently_logged_in_user(
                self, client, logged_in_test_user, test_calendar
        ):
            another_user = User.objects.create_user(
                    username='another_user',
                    email='anotheruser@gmail.com',
                    password='asdfasdf@9394'
            )
            another_users_calendar = Calendar.objects.create(
                    google_id='id_another_user_calendar',
                    name='another_user_calendar',
                    user=another_user
            )
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  summary="DONT DISPLAY - Another user's event",
                  calendar=another_users_calendar,
                  start=timezone.now() + timedelta(hours=2),
                  end=not_used).save()

            # Logged in user's event
            Event(google_id='2',
                  summary="DO DISPLAY - Logged in user's event",
                  calendar=test_calendar,
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()

            response = client.get('/')

            assert 'main_event' in response.context
            assert response.context['main_event'].summary == \
                   "DO DISPLAY - Logged in user's event"

            assert 'other_events' in response.context
            assert len(response.context['other_events']) == 0

        @pytest.mark.skip('TODO')
        def test_return_only_events_for_active_calendars(
                self, client, logged_in_test_user
        ):
            pass


class TestRefreshEvents:
    def test_returns_error_if_user_not_logged_in(self, client):
        response = client.post('/events/refresh/')
        assertContains(response,
                       "Please log in before refreshing!",
                       status_code=401)

    @patch.object(timers.views, 'refresh_events')
    def test_refreshes_the_events_of_logged_in_user(
            self, refresh_events_mock, logged_in_test_user, client
    ):
        response = client.post('/events/refresh/')

        assertContains(response, "Ok", status_code=200)
        refresh_events_mock.assert_called_with(logged_in_test_user)


class TestRefreshCalendars:
    def test_returns_error_if_user_not_logged_in(self, client):
        response = client.post('/calendars/refresh/')
        assertContains(response,
                       "Please log in before refreshing!",
                       status_code=401)

    @patch.object(timers.views, 'refresh_calendars')
    def test_refreshes_the_events_of_logged_in_user(
            self, refresh_calendars_mock, logged_in_test_user, client
    ):
        response = client.post('/calendars/refresh/')

        assertContains(response, "Ok", status_code=200)
        refresh_calendars_mock.assert_called_with(logged_in_test_user)
