from django.contrib import admin

# Register your models here.
from timers.models import Event, Calendar


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'calendar_name', 'start')

    def user(self, obj):
        return obj.calendar.user

    def calendar_name(self, obj):
        return obj.calendar.name


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'active')
