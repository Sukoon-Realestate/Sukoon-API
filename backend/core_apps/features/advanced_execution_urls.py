from django.urls import path
from . import advanced_execution_views as views

urlpatterns = [
    path("advanced-executions/", views.inbox),
    path("advanced-executions/<uuid:execution_id>/", views.detail),
    path("advanced-executions/<uuid:execution_id>/<str:action>/", views.action),
]
