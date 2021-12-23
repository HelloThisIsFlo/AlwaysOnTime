from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils.timezone import now

from timers.models import Calendar, Event

pytestmark = pytest.mark.django_db


class TestCalendar:
    def test_can_not_save_2_calendars_with_same_google_id_for_same_user(
            self, test_user
    ):
        Calendar.objects.create(google_id='unique_id',
                                name='cal1',
                                user=test_user)
        with pytest.raises(IntegrityError) as e:
            with transaction.atomic():
                Calendar.objects.create(google_id='unique_id',
                                        name="another cal with same"
                                             " 'google_id'",
                                        user=test_user)

        assert 'UNIQUE constraint failed' in str(e.value)
        assert Calendar.objects.count() == 1

    def test_can_save_2_calendars_with_same_google_id_for_different_users(
            self, test_user, another_user
    ):
        Calendar.objects.create(google_id='unique_id',
                                name='cal1',
                                user=test_user)
        # Should not raise
        Calendar.objects.create(google_id='unique_id',
                                name="another cal with same 'google_id'"
                                     'but different user',
                                user=another_user)

        assert Calendar.objects.count() == 2


class TestEvent:
    def test_can_not_save_2_events_with_same_google_id_for_same_calendar(
            self, test_user_calendar, another_user_calendar
    ):
        start = now()
        end = start + timedelta(hours=1)
        Event.objects.create(google_id='unique_id',
                             name='event1',
                             start=start,
                             end=end,
                             calendar=test_user_calendar)

        with pytest.raises(IntegrityError) as e:
            with transaction.atomic():
                Event.objects.create(google_id='unique_id',
                                     name="another event with same 'google_id'",
                                     start=start,
                                     end=end,
                                     calendar=test_user_calendar)

        assert 'UNIQUE constraint failed' in str(e.value)
        assert Event.objects.count() == 1

    def test_can_save_2_events_with_same_google_id_for_different_calendars(
            self, test_user_calendar, another_user_calendar
    ):
        start = now()
        end = start + timedelta(hours=1)
        Event.objects.create(google_id='unique_id',
                             name='event1',
                             start=start,
                             end=end,
                             calendar=test_user_calendar)
        # Should not raise
        Event.objects.create(google_id='unique_id',
                             name="another event with same 'google_id'"
                                  " but different user's calendar",
                             start=start,
                             end=end,
                             calendar=another_user_calendar)

        assert Event.objects.count() == 2
