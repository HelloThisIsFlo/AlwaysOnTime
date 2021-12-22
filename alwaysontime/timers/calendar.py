from datetime import timedelta

from allauth.socialaccount.models import SocialToken
from django.utils import timezone

from timers.google_api import GoogleCalendarApi
from timers.models import Event, Calendar


def refresh_events(user):
    social_token = SocialToken.objects.filter(account__user=user).get()
    calendar_api = GoogleCalendarApi(token=social_token.token,
                                     refresh_token=social_token.token_secret)
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
