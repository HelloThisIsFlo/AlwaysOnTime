# Create your tests here.
import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
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
                self, client, logged_in_test_user, test_user_calendar
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  name='Starts in 4 hours',
                  calendar=test_user_calendar,
                  start=timezone.now() + timedelta(hours=4),
                  end=not_used).save()
            Event(google_id='2',
                  name='Starts in 1 minutes: This is the next one in time',
                  calendar=test_user_calendar,
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()
            Event(google_id='3',
                  name='Starts in 2 hours',
                  calendar=test_user_calendar,
                  start=timezone.now() + timedelta(hours=2),
                  end=not_used).save()

            response = client.get('/')

            assert 'main_event' in response.context
            assert response.context['main_event'].name == \
                   'Starts in 1 minutes: This is the next one in time'

            assert 'other_events' in response.context
            other_events = response.context['other_events']
            assert len(other_events) == 2
            assert other_events[0].name == 'Starts in 2 hours'
            assert other_events[1].name == 'Starts in 4 hours'

        def test_return_only_main_event_if_no_other_events(
                self, client, logged_in_test_user, test_user_calendar
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  name='Starts in 1 minutes: This is the next one in time',
                  calendar=test_user_calendar,
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
                self, client, logged_in_test_user, test_user_calendar,
                another_user, another_user_calendar
        ):
            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  name="DONT DISPLAY - Another user's event",
                  calendar=another_user_calendar,
                  start=timezone.now() + timedelta(hours=2),
                  end=not_used).save()

            # Logged in user's event
            Event(google_id='2',
                  name="DO DISPLAY - Logged in user's event",
                  calendar=test_user_calendar,
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()

            response = client.get('/')

            assert response.context['main_event'].name == \
                   "DO DISPLAY - Logged in user's event"
            assert len(response.context['other_events']) == 0

        def test_return_only_events_for_active_calendars(
                self, client, logged_in_test_user, test_user_calendar
        ):
            inactive_calendar = Calendar.objects.create(
                    google_id='id_another_user_calendar',
                    name='another_user_calendar',
                    user=logged_in_test_user,
                    active=False
            )

            not_used = timezone.now() + timedelta(hours=10)
            Event(google_id='1',
                  name="DONT DISPLAY - Event from inactive calendar",
                  calendar=inactive_calendar,
                  start=timezone.now() + timedelta(hours=2),
                  end=not_used).save()

            # Logged in user's event
            Event(google_id='2',
                  name="DO DISPLAY - Event from active calendar",
                  calendar=test_user_calendar,
                  start=timezone.now() + timedelta(minutes=1),
                  end=not_used).save()

            response = client.get('/')

            assert response.context['main_event'].name == \
                   "DO DISPLAY - Event from active calendar"
            assert len(response.context['other_events']) == 0

    class TestLayout:
        def test_has_link_to_settings_page(self, client, logged_in_test_user):
            response = client.get('/')
            assertContains(response,
                           f'<a href="{reverse("settings")}">Settings</a>')


class TestSettings:
    def test_redirects_if_user_not_logged_in(self, client):
        response = client.get('/settings/')
        assertRedirects(response, '/accounts/login/?next=/settings/')

    def test_redirects_if_user_does_not_have_google_linked(
            self, test_user_without_google_credentials, client
    ):
        client.login(username=conftest.TEST_USERNAME,
                     password=conftest.TEST_PASSWORD)
        response = client.get('/settings/')
        assertRedirects(response, '/accounts/social/connections/')

    def test_use_correct_template(
            self, logged_in_test_user, client
    ):
        response = client.get('/settings/')
        assertTemplateUsed(response, 'settings.html')

    def test_return_all_users_calendars_with_status(
            self, logged_in_test_user, client
    ):
        Calendar.objects.create(id=1,
                                google_id='google_id_1',
                                name='cal1',
                                active=False,
                                user=logged_in_test_user)
        Calendar.objects.create(id=2,
                                google_id='google_id_2',
                                name='cal2',
                                active=True,
                                user=logged_in_test_user)
        Calendar.objects.create(id=3,
                                google_id='google_id_3',
                                name='cal3',
                                active=False,
                                user=logged_in_test_user)
        response = client.get('/settings/')
        assert 'calendars' in response.context
        assert response.context['calendars'] == [
            {'id': 1, 'name': 'cal1', 'active': False},
            {'id': 2, 'name': 'cal2', 'active': True},
            {'id': 3, 'name': 'cal3', 'active': False},
        ]

    def test_return_empty_list_of_calendars_if_no_calendars(
            self, logged_in_test_user, client
    ):
        Calendar.objects.all().delete()
        response = client.get('/settings/')
        assert 'calendars' in response.context
        assert response.context['calendars'] == []

    def test_only_return_calendars_of_logged_in_user(
            self, logged_in_test_user, another_user, client
    ):
        Calendar.objects.create(id=1,
                                google_id='google_id_1',
                                name='cal1',
                                active=False,
                                user=logged_in_test_user)
        Calendar.objects.create(id=2,
                                google_id='google_id_2',
                                name='cal2',
                                active=True,
                                user=logged_in_test_user)
        Calendar.objects.create(id=3,
                                google_id='google_id_3',
                                name='should not be displayed <- another user',
                                active=False,
                                user=another_user)

        response = client.get('/settings/')

        assert 'calendars' in response.context
        assert response.context['calendars'] == [
            {'id': 1, 'name': 'cal1', 'active': False},
            {'id': 2, 'name': 'cal2', 'active': True}
        ]

    def test_has_link_to_home_page(self, client, logged_in_test_user):
        response = client.get('/settings/')
        assertContains(response,
                       f'<a href="{reverse("index")}">Home</a>')


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


class TestUpdateCalendar:
    def test_set_calendar_as_active(
            self, client, logged_in_test_user, test_user_calendar):
        test_user_calendar.active = False
        test_user_calendar.save()

        response = client.post(f'/calendars/{test_user_calendar.id}/',
                               json.dumps({'active': True}),
                               content_type="application/json")

        assertContains(response, "Ok", status_code=200)
        calendar = Calendar.objects.get(id=test_user_calendar.id)
        assert calendar.active

    def test_returns_error_if_user_not_logged_in(
            self, client, test_user_calendar
    ):
        test_user_calendar.active = False
        test_user_calendar.save()

        response = client.post(f'/calendars/{test_user_calendar.id}/',
                               json.dumps({'active': True}),
                               content_type="application/json")

        assertContains(response,
                       "Please log in!",
                       status_code=401)

        calendar = Calendar.objects.get(id=test_user_calendar.id)
        assert not calendar.active

    def test_returns_error_if_missing_parameter(
            self, client, logged_in_test_user, test_user_calendar
    ):
        response = client.post(f'/calendars/{test_user_calendar.id}/',
                               json.dumps({}),
                               content_type="application/json")
        assertContains(response,
                       "Missing 'active' parameter!",
                       status_code=400)

    def test_returns_error_if_calendar_doesnt_exist(
            self, client, logged_in_test_user
    ):
        response = client.post('/calendars/1234/',
                               json.dumps({'active': True}),
                               content_type="application/json")
        assertContains(response,
                       "No calendar with id '1234'",
                       status_code=404)

    def test_can_only_set_calendars_for_logged_in_user(
            self, client, logged_in_test_user,
            another_user, another_user_calendar
    ):
        another_user_calendar.active = False
        another_user_calendar.save()

        response = client.post(f'/calendars/{another_user_calendar.id}/',
                               json.dumps({'active': True}),
                               content_type="application/json")

        assertContains(response,
                       f"No calendar with id '{another_user_calendar.id}'",
                       status_code=404)
        cal = Calendar.objects.get(id=another_user_calendar.id)
        assert not cal.active
