# Create your tests here.
from datetime import timedelta
from unittest.mock import patch

from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from timers.models import Event

TEST_PASSWORD = 'testuser1234@'
TEST_USERNAME = 'testuser'
TEST_GOOGLE_TOKEN = 'abcdefg123456'


def create_test_user():
    test_user = User.objects.create_user(
            username=TEST_USERNAME,
            email='testuser@gmail.com',
            password=TEST_PASSWORD
    )
    SocialToken.objects.create(
            account=SocialAccount.objects.create(user=test_user),
            app=SocialApp.objects.create(),
            token=TEST_GOOGLE_TOKEN,
    )
    return test_user


class HomePage_FailureScenario(TestCase):
    def setUp(self):
        User.objects.create_user(
                username=TEST_USERNAME,
                email='testuser@gmail.com',
                password=TEST_PASSWORD
        )

    def test_redirects_if_user_not_logged_in(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_redirects_if_user_does_not_have_google_linked(self):
        self.client.login(username=TEST_USERNAME,
                          password=TEST_PASSWORD)
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/social/connections/')

    def test_show_error_if_user_didnt_give_necessary_permissions(self):
        # TODO
        pass


class HomePage_SuccessScenario(TestCase):
    def setUp(self):
        create_test_user()
        self.client.login(username=TEST_USERNAME,
                          password=TEST_PASSWORD)

    def test_shows_home_page(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'index.html')

    def test_return_next_event_in_time_as_main_event_and_rest_as_other_events(
            self):
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

        response = self.client.get('/')

        self.assertIn('main_event', response.context)
        self.assertEqual(
                response.context['main_event'].summary,
                'Starts in 1 minutes: This is the next one in time'
        )

        self.assertIn('other_events', response.context)
        other_events = response.context['other_events']
        self.assertEqual(len(other_events), 2)
        self.assertEqual(
                other_events[0].summary,
                'Starts in 2 hours'
        )
        self.assertEqual(
                other_events[1].summary,
                'Starts in 4 hours'
        )

    def test_return_only_main_event_if_no_other_events(self):
        not_used = timezone.now() + timedelta(hours=10)
        Event(google_id='1',
              summary='Starts in 1 minutes: This is the next one in time',
              start=timezone.now() + timedelta(minutes=1),
              end=not_used).save()

        response = self.client.get('/')

        self.assertIn('main_event', response.context)
        self.assertIsNotNone(response.context['main_event'])

        self.assertIn('other_events', response.context)
        self.assertEqual(len(response.context['other_events']), 0)

    def test_return_none_if_no_events_at_all(self):
        response = self.client.get('/')

        self.assertIn('main_event', response.context)
        self.assertIsNone(response.context['main_event'])

        self.assertIn('other_events', response.context)
        self.assertEqual(len(response.context['other_events']), 0)


class RefreshEvents(TestCase):
    def setUp(self):
        refresh_all_events_patcher = \
            patch('timers.views.refresh_all_events')
        self.refresh_all_events_mock = refresh_all_events_patcher.start()
        self.addCleanup(refresh_all_events_patcher.stop)

        self.test_user = create_test_user()

    def test_returns_error_if_user_not_logged_in(self):
        response = self.client.post('/events/refresh/')
        self.assertContains(response,
                            "Please log in before refreshing!",
                            status_code=401)

    def test_refreshes_the_events_of_logged_in_user(self):
        self.client.login(username=TEST_USERNAME,
                          password=TEST_PASSWORD)
        response = self.client.post('/events/refresh/')

        self.assertContains(response, "Ok", status_code=200)
        self.refresh_all_events_mock.assert_called_with(self.test_user)
