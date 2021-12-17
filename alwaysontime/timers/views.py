import datetime
from functools import wraps
from math import floor

import dateutil.parser
import requests
from allauth.socialaccount.models import SocialToken
from alwaysontime.settings import GOOGLE_SCOPES
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ICE_CREAM_CALENDAR_ID = 'c_u2p0q67mc81rqekasjdtu83ng4@group.calendar.google.com'


def build_authenticated_service(endpoint_func):
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
        'token': 'yoooooooo not token'
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
@build_authenticated_service
def sandbox(request, service):
    # list_calendars(service)

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    print('Getting the upcoming 10 events')
    events_result = service \
        .events() \
        .list(calendarId=ICE_CREAM_CALENDAR_ID) \
        .execute()
    events_result = service.events().list(calendarId=ICE_CREAM_CALENDAR_ID,
                                          timeMin=now,
                                          maxResults=10,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        print()
        summary = event['summary']
        start = dateutil.parser.isoparse(event['start']['dateTime'])
        end = dateutil.parser.isoparse(event['end']['dateTime'])
        duration = end - start
        duration_h = floor(duration.total_seconds() / 3600)
        duration_m = floor((duration.total_seconds() / 60) - (duration_h * 60))
        print(f'{summary=}')
        print(f'{start=}')
        print(f'{end=}')
        print(f'{duration=}')
        print(f'formatted_duration={duration_h}h{duration_m}m')
        print(event)
        print()

    return redirect('index')


def list_calendars(service):
    print("Listing all calendars")
    calendar_list_result = service.calendarList().list().execute()
    calendars = calendar_list_result.get('items', [])
    for c in calendars:
        print(f"{c['id']=} {c['summary']=}")
