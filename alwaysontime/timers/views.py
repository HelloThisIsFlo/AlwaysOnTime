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
    refresh_all_events_in_shared_calendar_in_the_background
from timers.models import Event


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

    refresh_all_events_in_shared_calendar_in_the_background()

    now = timezone.now()
    now_minus_delta = \
        now - datetime.timedelta(minutes=settings.TIMERS_SHOW_X_MIN_PAST)
    now_plus_delta = \
        now + datetime.timedelta(minutes=settings.TIMERS_SHOW_X_MIN_FUTURE)
    events = Event.objects.filter(
            start__gte=now_minus_delta,
            start__lt=now_plus_delta
    ).order_by('start')

    # TODO: Separate 'main_event' (soonest to happen) from other_events'
    #       To make formatting easier
    return render(request, 'index.html', {
        'events': events
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
    # Do nothing
    return redirect('index')


def list_calendars(service):
    print("Listing all calendars")
    calendar_list_result = service.calendarList().list().execute()
    calendars = calendar_list_result.get('items', [])
    for c in calendars:
        print(f"{c['id']=} {c['summary']=}")
