from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Event(models.Model):
    google_id = models.CharField(max_length=100, primary_key=True)
    summary = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()


class Calendar(models.Model):
    google_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
