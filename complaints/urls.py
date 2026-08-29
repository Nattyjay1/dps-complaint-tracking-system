from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("complaints/", views.complaint_list, name="complaint_list"),
    path("complaints/new/", views.complaint_create, name="complaint_create"),
    path("complaints/reports/resolved/", views.resolved_report, name="resolved_report"),
    path("complaints/<str:complaint_id>/", views.complaint_detail, name="complaint_detail"),
]
