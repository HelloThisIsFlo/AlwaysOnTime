from django.contrib.auth.models import User


def refresh_all_events_in_shared_calendar():
    User.objects.get(email__iexact='flori@nkempenich.com')

