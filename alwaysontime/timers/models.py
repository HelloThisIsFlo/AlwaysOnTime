from django.db import models


# Create your models here.

class Event(models.Model):
    google_id = models.CharField(max_length=100, primary_key=True)
    summary = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
