from django.urls import path
from . import views
from .preparation import TasksView
from .action_center import ActionCenterView
from . import quality
from . import discovery
from .calendar import ViewingCalendarView
from . import suggestions

urlpatterns = [
    path("experience/capabilities/", views.CapabilitiesView.as_view()),
    path("experience/preferences/", views.PersonalPreferencesView.as_view()),
    path("experience/preparation-tasks/", TasksView.as_view()),
    path("action-center/", ActionCenterView.as_view()),
    path("experience/listing-assessments/", quality.CreateView.as_view()),
    path(
        "experience/listing-assessments/<uuid:identity>/", quality.DetailView.as_view()
    ),
    path("experience/discovery-preferences/", discovery.SettingsViewView.as_view()),
    path("experience/discovery-interactions/", discovery.InteractionView.as_view()),
    path(
        "experience/viewings/<uuid:identity>/calendar/", ViewingCalendarView.as_view()
    ),
    path("experience/suggestions/", suggestions.SuggestionsView.as_view()),
    path("experience/alternatives/", suggestions.AlternativesView.as_view()),
]
