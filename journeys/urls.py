from django.urls import path

from . import views

app_name = "journeys"

urlpatterns = [
    path("", views.journey_home, name="journey_home"),
    path("onboarding/goal/", views.onboarding_goal, name="onboarding_goal"),
    path("onboarding/framework/", views.onboarding_framework, name="onboarding_framework"),
    path("onboarding/start/<uuid:framework_id>/<str:goal_type>/", views.onboarding_start, name="onboarding_start"),
    path("steps/<uuid:step_id>/complete/", views.step_mark_complete, name="step_mark_complete"),
    path("steps/<uuid:step_id>/interview/start/", views.interview_start, name="interview_start"),
    path("interviews/<uuid:session_id>/", views.interview_session_view, name="interview_session"),
    path("information-requests/", views.information_request_list, name="information_request_list"),
    path("information-requests/new/", views.information_request_create, name="information_request_create"),
    path("information-requests/new/<uuid:step_id>/", views.information_request_create, name="information_request_create_for_step"),
    path("information-requests/respond/<uuid:token>/", views.information_request_respond, name="information_request_respond"),
]
