from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.BohlaleLoginView.as_view(), name="login"),
    path("logout/", views.BohlaleLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/export/", views.export_my_data, name="export_my_data"),
    path("profile/deactivate/", views.deactivate_account, name="deactivate_account"),
]
