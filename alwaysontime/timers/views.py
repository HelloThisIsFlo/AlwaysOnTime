import datetime
from functools import wraps

import dateutil.parser
import requests
from allauth.socialaccount.models import SocialToken
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from alwaysontime.settings import GOOGLE_SCOPES
from timers.models import Event

ICE_CREAM_CALENDAR_ID = 'c_u2p0q67mc81rqekasjdtu83ng4@group.calendar.google.com'


def with_authenticated_calendar_service(endpoint_func):
    @wraps(endpoint_func)
    def wrapped(request):
        social_token = SocialToken.objects.get(account__user=request.user)
        creds = Credentials(token=social_token.token,
                            refresh_token=social_token.token_secret,
                            token_uri='https://oauth2.googleapis.com/token',
                            client_id=social_token.app.client_id,
                            client_secret=social_token.app.secret,
                            scopes=GOOGLE_SCOPES)
        if creds.expired:
            creds.refresh(Request())
            print("Token refreshed!")

        try:
            service = build('calendar', 'v3', credentials=creds)
            resp = endpoint_func(request, service)

        except HttpError as error:
            print('An error occurred: %s' % error)
            return HttpResponse('An error occurred: %s' % error)

        return resp

    return wrapped


@login_required
def index(request):
    if not SocialToken.objects.filter(account__user=request.user):
        return redirect('/accounts/social/connections/')

    return render(request, 'index.html', {
        'events': list(Event.objects.all())
    })


@login_required
def revoke(request):
    social_token = SocialToken.objects.get(account__user=request.user)
    requests.post('https://oauth2.googleapis.com/revoke',
                  params={'token': social_token.token},
                  headers={'content-type': 'application/x-www-form-urlencoded'})
    logout(request)
    return redirect('index')


@login_required
@with_authenticated_calendar_service
def refresh_events_in_db(request, calendar_service):
    def to_utc_str(dt):
        return dt.isoformat() + 'Z'

    def parse(dt):
        return dateutil.parser.isoparse(dt)

    now = datetime.datetime.utcnow()
    now_plus_2_days = datetime.datetime.utcnow() + datetime.timedelta(days=2)
    now_minus_1_hour = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    events = calendar_service \
        .events() \
        .list(calendarId=ICE_CREAM_CALENDAR_ID,
              timeMin=to_utc_str(now),
              timeMax=to_utc_str(now_plus_2_days),
              maxResults=10,
              singleEvents=True,
              orderBy='startTime') \
        .execute() \
        .get('items', [])

    for event in events:
        google_id = event['id']
        if not Event.objects.filter(google_id=google_id).exists():
            event = Event(google_id=google_id,
                          summary=(event['summary']),
                          start=(parse(event['start']['dateTime'])),
                          end=(parse(event['end']['dateTime'])))
            event.save()

    # TODO: Delete events that are 1h in the past see: 'now_minus_1_hour'
    return redirect('index')


@login_required
@with_authenticated_calendar_service
def sandbox(request, calendar_service):
    # Do nothing
    return redirect('index')


def list_calendars(service):
    print("Listing all calendars")
    calendar_list_result = service.calendarList().list().execute()
    calendars = calendar_list_result.get('items', [])
    for c in calendars:
        print(f"{c['id']=} {c['summary']=}")
