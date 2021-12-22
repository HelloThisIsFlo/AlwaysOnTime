from datetime import timedelta

from allauth.socialaccount.models import SocialToken
from django.utils import timezone

from timers.google_api import GoogleCalendarApi
from timers.models import Event, Calendar


def refresh_events(user):
    calendar_api = _get_calendar_api_for(user)
    active_calendars = list(Calendar.objects.filter(user=user, active=True))
    now = timezone.now()
    for cal in active_calendars:
        events = calendar_api.events(
                cal.google_id,
                before=now - timedelta(hours=1),
                after=now + timedelta(days=2),
                order_by='startTime'
        )
        for event in events:
            event = Event(google_id=event['id'],
                          summary=event['summary'],
                          start=event['start'],
                          end=event['end'],
                          calendar=cal)
            event.save()

        all_event_ids = [e['id'] for e in events]
        Event.objects.exclude(google_id__in=all_event_ids).delete()


def _get_calendar_api_for(user):
    social_token = SocialToken.objects.filter(account__user=user).get()
    calendar_api = GoogleCalendarApi(token=social_token.token,
                                     refresh_token=social_token.token_secret)
    return calendar_api


def refresh_calendars(user):
    calendar_api = _get_calendar_api_for(user)
    calendars = calendar_api.calendars()
    for cal in calendars:
        cal_id = cal['id']
        if Calendar.objects.filter(google_id=cal_id).exists():
            calendar = Calendar.objects.get(google_id=cal_id)
            calendar.name = cal['name']
        else:
            calendar = Calendar(google_id=cal_id,
                                name=cal['name'],
                                user=user,
                                active=False)
        calendar.save()

    all_calendar_ids = [c['id'] for c in calendars]
    for calendar in Calendar.objects.exclude(google_id__in=all_calendar_ids):
        calendar.active = False
        calendar.save()
