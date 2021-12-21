import datetime
from threading import Thread

import dateutil.parser
from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from alwaysontime.settings import GOOGLE_SCOPES
from timers.models import Event


def refresh_all_events_in_shared_calendar_in_the_background():
    Thread(target=refresh_all_events_in_shared_calendar, daemon=True).start()


def refresh_all_events_in_shared_calendar():
    events = _load_events_from_calendar()
    replace_all_events_in_db(events)


def refresh_all_events(user):
    pass


def replace_all_events_in_db(events):
    Event.objects.all().delete()
    for event in events:
        event = Event(google_id=(event['id']),
                      summary=(event['summary']),
                      start=(_parse(event['start']['dateTime'])),
                      end=(_parse(event['end']['dateTime'])))
        event.save()


def _load_events_from_calendar():
    def to_google_format(dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        creds = _get_credentials()
        calendar_service = build('calendar', 'v3', credentials=creds)

        now = timezone.now()
        now_minus_1_hour = now - datetime.timedelta(days=1)
        now_plus_7_days = now + datetime.timedelta(days=7)
        return calendar_service \
            .events() \
            .list(calendarId=settings.SHARED_CALENDAR_ID,
                  timeMin=to_google_format(now_minus_1_hour),
                  timeMax=to_google_format(now_plus_7_days),
                  maxResults=100,
                  singleEvents=True,
                  orderBy='startTime') \
            .execute() \
            .get('items', [])

    except HttpError as error:
        print('An error occurred: %s' % error)
        return []


def _get_credentials():
    social_token = SocialToken \
        .objects \
        .filter(account__user__email__iexact=settings.SHARED_CALENDAR_OWNER) \
        .get()
    creds = Credentials(token=social_token.token,
                        refresh_token=social_token.token_secret,
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=social_token.app.client_id,
                        client_secret=social_token.app.secret,
                        scopes=GOOGLE_SCOPES)
    if creds.expired:
        creds.refresh(Request())
        print("Token refreshed!")
    return creds


def _to_utc_str(dt):
    return dt.isoformat() + 'Z'


def _parse(dt):
    return dateutil.parser.isoparse(dt)
