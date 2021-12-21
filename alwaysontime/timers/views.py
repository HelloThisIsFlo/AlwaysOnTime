import datetime
from functools import wraps

import requests
from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from alwaysontime.settings import GOOGLE_SCOPES
from timers.domain import calendar
from timers.domain.calendar import \
    refresh_all_events_in_shared_calendar_in_the_background, refresh_all_events
from timers.models import Event


def with_authenticated_calendar_service(endpoint_func):
    @wraps(endpoint_func)
    def wrapper(request):
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

    return wrapper


@login_required
def index(request):
    if not SocialToken.objects.filter(account__user=request.user):
        return redirect('/accounts/social/connections/')

    refresh_all_events_in_shared_calendar_in_the_background()

    now = timezone.now()
    now_minus_delta = \
        now - datetime.timedelta(minutes=settings.TIMERS_SHOW_X_MIN_PAST)
    now_plus_delta = \
        now + datetime.timedelta(minutes=settings.TIMERS_SHOW_X_MIN_FUTURE)
    events = list(Event.objects.filter(
            start__gte=now_minus_delta,
            start__lt=now_plus_delta
    ).order_by('start'))

    return render(request, 'index.html', {
        'main_event': events[0] if events else None,
        'other_events': events[1:]
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
def refresh_events_in_db(request):
    calendar.refresh_all_events_in_shared_calendar()
    return redirect('index')


@login_required
@with_authenticated_calendar_service
def sandbox(request, calendar_service):
    def to_google_format(dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    list_calendars(calendar_service)

    now = timezone.now()
    now_minus_1_hour = now - datetime.timedelta(days=1)
    now_plus_7_days = now + datetime.timedelta(days=7)
    events = calendar_service \
        .events() \
        .list(calendarId='primary',
              timeMin=to_google_format(now_minus_1_hour),
              timeMax=to_google_format(now_plus_7_days),
              maxResults=100,
              singleEvents=True,
              orderBy='startTime') \
        .execute() \
        .get('items', [])

    return HttpResponse(f'{events=}')


def list_calendars(service):
    print("Listing all calendars")
    calendar_list_result = service.calendarList().list().execute()
    calendars = calendar_list_result.get('items', [])
    for c in calendars:
        print(f"{c['id']=} {c['summary']=}")


def events_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse("Please log in before refreshing!", status=401)
    refresh_all_events(request.user)
    return HttpResponse("Ok")
