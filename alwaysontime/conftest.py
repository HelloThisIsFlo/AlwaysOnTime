import pytest
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
from django.conf import settings
from django.contrib.auth.models import User

from timers.models import Calendar

TEST_PASSWORD = 'testuser1234@'
TEST_USERNAME = 'testuser'
TEST_CALENDAR_ID = 'test_calendar_id'
TEST_GOOGLE_TOKEN = 'abcdefg123456'
TEST_GOOGLE_REFRESH_TOKEN = 'zyxvgadf482'
TEST_GOOGLE_APP_CLIENT_ID = 'google_app_client_id'
TEST_GOOGLE_APP_SECRET = 'google_app_client_secret'


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
                    user=test_user
            ),
            app=SocialApp.objects.create(
                    name=settings.GOOGLE_APP_NAME,
                    client_id=TEST_GOOGLE_APP_CLIENT_ID,
                    secret=TEST_GOOGLE_APP_SECRET
            ),
            token=TEST_GOOGLE_TOKEN,
            token_secret=TEST_GOOGLE_REFRESH_TOKEN
    )
    return test_user


@pytest.fixture
def logged_in_test_user(test_user, client):
    client.login(
            username=TEST_USERNAME,
            password=TEST_PASSWORD
    )
    return test_user


@pytest.fixture
def test_user_calendar(test_user):
    return Calendar.objects.create(
            google_id=TEST_CALENDAR_ID,
            active=True,
            name='test_calendar',
            user=test_user
    )


@pytest.fixture
def another_user():
    return User.objects.create_user(
            username='another_user',
            email='anotheruser@gmail.com',
            password='asdfasdf@9394'
    )


@pytest.fixture
def another_users_calendar(another_user):
    return Calendar.objects.create(
            google_id='id_another_user_calendar',
            name='another_user_calendar',
            user=another_user,
            active=True
    )
