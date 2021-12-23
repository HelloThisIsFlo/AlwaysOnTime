from django.urls import path

from timers import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sandbox/', views.sandbox, name='sandbox'),
    path('revoke/', views.revoke, name='revoke'),
    path('refresh_events_in_db/',
         views.refresh_events_in_db,
         name='refresh_events_in_db'),
    path('events/refresh/', views.events_refresh, name='events_refresh'),
    path('calendars/refresh/',
         views.calendars_refresh,
         name='calendars_refresh'),
    path('calendars/<int:cal_id>/',
         views.calendars_update,
         name='calendars_update'),
    path('settings/', views.settings_page, name='settings')
]
