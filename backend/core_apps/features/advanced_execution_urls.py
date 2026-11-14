from django.urls import path
from . import advanced_execution_views as views

urlpatterns = [
    path("advanced-executions/", views.InboxView.as_view()),
    path("advanced-executions/<uuid:execution_id>/", views.DetailView.as_view()),
    path(
        "advanced-executions/<uuid:execution_id>/<str:action>/",
        views.ActionView.as_view(),
    ),
]
