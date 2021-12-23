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
        for e in events:
            e_id = e['id']
            if Event.objects.filter(google_id=e_id, calendar=cal).exists():
                event = Event.objects.get(google_id=e_id, calendar=cal)
            else:
                event = Event(google_id=e_id)
            event.name = e['name']
            event.start = e['start']
            event.end = e['end']
            event.calendar = cal
            event.save()

        all_event_ids_returned_by_google = [e['id'] for e in events]
        Event.objects \
            .filter(calendar=cal) \
            .exclude(google_id__in=all_event_ids_returned_by_google) \
            .delete()


def _get_calendar_api_for(user):
    social_token = SocialToken.objects.filter(account__user=user).get()
    return GoogleCalendarApi(token=social_token.token,
                             refresh_token=social_token.token_secret)


def refresh_calendars(user):
    calendar_api = _get_calendar_api_for(user)
    calendars = calendar_api.calendars()
    for cal in calendars:
        cal_id = cal['id']
        if Calendar.objects.filter(google_id=cal_id, user=user).exists():
            calendar = Calendar.objects.get(google_id=cal_id, user=user)
        else:
            calendar = Calendar(google_id=cal_id, user=user, active=False)
        calendar.name = cal['name']
        calendar.save()

    all_calendar_ids = [c['id'] for c in calendars]

    calendars_not_returned_by_google = Calendar.objects \
        .filter(user=user) \
        .exclude(google_id__in=all_calendar_ids)

    for calendar in calendars_not_returned_by_google:
        calendar.active = False
        calendar.save()
