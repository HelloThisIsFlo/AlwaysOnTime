from allauth.socialaccount.models import SocialApp
from django.conf import settings
from google.oauth2.credentials import Credentials


class GoogleCalendarApi:
    def __init__(self, token, refresh_token):
        google_app = SocialApp.objects.get(name=settings.GOOGLE_APP_NAME)

        Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=google_app.client_id,
                client_secret=google_app.secret,
                scopes=settings.GOOGLE_SCOPES
        )

    def events(self, calendar_id, before, after, order_by):
        pass
