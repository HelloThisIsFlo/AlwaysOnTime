from datetime import timezone, timedelta

import dateutil.parser
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
        self.calendar_service = build('calendar', 'v3', credentials=creds)

    def events(self, calendar_id, before, after, order_by):
        def to_google_format(dt):
            return dt.astimezone(timezone(timedelta(0))).strftime(
                    '%Y-%m-%dT%H:%M:%SZ')

        if not before.tzinfo or not after.tzinfo:
            raise RuntimeError("Make sure to set 'tzinfo' in "
                               "'before' and 'after' parameters")

        events_from_google = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=to_google_format(before),
                timeMax=to_google_format(after),
                maxResults=100,
                singleEvents=True,
                orderBy=order_by
        ).execute().get('items', [])

        return [self._map_event_to_domain(e) for e in events_from_google]

    def calendars(self):
        calendars_from_google = \
            self.calendar_service \
                .calendarList() \
                .list() \
                .execute() \
                .get('items', [])
        return [self._map_calendar_to_domain(c) for c in calendars_from_google]

    @staticmethod
    def _map_event_to_domain(event):
        def parse_date(date_str):
            return dateutil.parser.isoparse(date_str)

        return {
            'id': event['id'],
            'name': event['summary'],
            'start': parse_date(event['start']['dateTime']),
            'end': parse_date(event['end']['dateTime'])
        }

    @staticmethod
    def _map_calendar_to_domain(calendar):
        return {'id': calendar['id'],
                'name': calendar['summary']}
