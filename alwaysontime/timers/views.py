import datetime
import json
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
from ratelimit.decorators import ratelimit

from alwaysontime.settings import GOOGLE_SCOPES
from timers.calendar import refresh_events, refresh_calendars
from timers.models import Event, Calendar


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


def google_account_required(view_func):
    @wraps(view_func)
    def wrapper(request):
        if not request.user.is_authenticated:
            raise RuntimeError("Only use this decorator in combination "
                               "with '@login_required'")
        if not SocialToken.objects.filter(account__user=request.user):
            return redirect('/accounts/social/connections/')
        return view_func(request)

    return wrapper


@login_required
@google_account_required
def index(request):
    now = timezone.now()
    now_minus_delta = \
        now - datetime.timedelta(minutes=settings.TIMERS_SHOW_X_MIN_PAST)
    now_plus_delta = \
        now + datetime.timedelta(minutes=settings.TIMERS_SHOW_X_MIN_FUTURE)
    events = list(Event.objects.filter(
            calendar__active=True,
            calendar__user=request.user,
            start__gte=now_minus_delta,
            start__lt=now_plus_delta
    ).order_by('start'))

    return render(request, 'index.html', {
        'main_event': events[0] if events else None,
        'other_events': events[1:]
    })


@login_required
@google_account_required
def settings_page(request):
    calendars = Calendar.objects.filter(user=request.user)
    return render(request, 'settings.html', {
        'calendars': [{
            'id': c.id,
            'name': c.name,
            'active': c.active
        } for c in calendars]
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
    # calendar.refresh_all_events_in_shared_calendar()
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


@ratelimit(key='user', rate='600/m', block=True)
def events_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse("Please log in before refreshing!", status=401)
    refresh_events(request.user)
    return HttpResponse("Ok")


@ratelimit(key='user', rate='600/m', block=True)
def calendars_refresh(request):
    if not request.user.is_authenticated:
        return HttpResponse("Please log in before refreshing!", status=401)
    refresh_calendars(request.user)
    return HttpResponse("Ok")


def calendars_update(request, cal_id):
    if not request.user.is_authenticated:
        return HttpResponse("Please log in!", status=401)

    params = json.loads(request.body)
    if 'active' not in params:
        return HttpResponse("Missing 'active' parameter!", status=400)

    if not Calendar.objects.filter(id=cal_id, user=request.user).exists():
        return HttpResponse(f"No calendar with id '{cal_id}'", status=404)

    calendar = Calendar.objects.get(id=cal_id)
    calendar.active = params['active']
    calendar.save()

    return HttpResponse("Ok")
