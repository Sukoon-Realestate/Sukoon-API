from django.urls import path
from . import views
from .preparation import tasks
from .action_center import action_center
from . import quality
from . import discovery
from .calendar import viewing_calendar
from . import suggestions

urlpatterns = [
    path('experience/capabilities/', views.capabilities),
    path('experience/preferences/', views.personal_preferences),
    path('experience/preparation-tasks/', tasks),
    path('action-center/', action_center),
    path('experience/listing-assessments/', quality.create),
    path('experience/listing-assessments/<uuid:identity>/', quality.detail),
    path('experience/discovery-preferences/', discovery.settings_view),
    path('experience/discovery-interactions/', discovery.interaction),
    path('experience/viewings/<uuid:identity>/calendar/', viewing_calendar),
    path('experience/suggestions/', suggestions.suggestions),
    path('experience/alternatives/', suggestions.alternatives),
]
