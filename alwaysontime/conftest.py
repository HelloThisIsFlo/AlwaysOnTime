import pytest
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
from django.contrib.auth.models import User

TEST_PASSWORD = 'testuser1234@'
TEST_USERNAME = 'testuser'
TEST_GOOGLE_TOKEN = 'abcdefg123456'


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
