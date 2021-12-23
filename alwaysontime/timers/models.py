from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Calendar(models.Model):
    google_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                    fields=('google_id', 'user'),
                    name="Unique 'google_id' per user"
            )
        ]


class Event(models.Model):
    google_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                    fields=('google_id', 'calendar'),
                    name="Unique 'google_id' per calendar"
            )
        ]
