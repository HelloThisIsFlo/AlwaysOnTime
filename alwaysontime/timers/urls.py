from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sandbox/', views.sandbox, name='sandbox'),
    path('revoke/', views.revoke, name='revoke'),
    path('load_events_in_db/',
         views.refresh_events_in_db,
         name='refresh_events_in_db'),
]
