from django.contrib import admin

# Register your models here.
from timers.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('summary', 'start')
