from django.urls import path
from . import asset_passport_views as views
from . import asset_analysis_views as analysis

urlpatterns = [
    path("asset-items/<uuid:asset_id>/review-workspace/", analysis.workspace),
    path("asset-items/<uuid:asset_id>/analysis/", analysis.create_analysis),
    path("asset-items/<uuid:asset_id>/shared-systems/", analysis.create_system),
    path("asset-items/<uuid:asset_id>/warranties/", analysis.create_warranty),
    path("asset-analysis-jobs/<uuid:record_id>/", analysis.job_detail),
    path("asset-analysis-jobs/<uuid:record_id>/cancel/", analysis.job_detail),
    path("asset-analysis-findings/<uuid:record_id>/review/", analysis.review_finding),
    path("asset-shared-systems/<uuid:record_id>/cases/", analysis.open_case),
    path("asset-pattern-cases/<uuid:record_id>/close/", analysis.close_case),
    path("asset-warranties/<uuid:record_id>/claim/", analysis.claim_warranty),
    path("asset-passport-destinations/", views.asset_destinations),
    path("properties/<uuid:property_id>/asset-items/", views.asset_items),
    path("properties/<uuid:property_id>/asset-spaces/", views.asset_spaces),
    path("asset-items/<uuid:asset_id>/", views.asset_detail),
    path("asset-items/<uuid:asset_id>/sources/", views.asset_sources),
    path("asset-items/<uuid:asset_id>/<str:action>/", views.asset_action),
]
