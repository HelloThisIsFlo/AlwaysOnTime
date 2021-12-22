from allauth.socialaccount.models import SocialApp
from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GoogleCalendarApi:
    def __init__(self, token, refresh_token):
        google_app = SocialApp.objects.get(name=settings.GOOGLE_APP_NAME)

        creds = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=google_app.client_id,
                client_secret=google_app.secret,
                scopes=settings.GOOGLE_SCOPES
        )
        if creds.expired:
            creds.refresh(Request())
        calendar_service = build('calendar', 'v3', credentials=creds)

    def events(self, calendar_id, before, after, order_by):
        pass
