from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("map/", views.map_view, name="map"),
    path("requests/", views.requests_page, name="requests"),
    path("messages/", views.messages_page, name="messages"),
    path("profile/", views.profile_page, name="profile"),
    path("donors/", views.donors_page, name="donors"),

    path("api/auth/login/", views.api_login, name="api_login"),
    path("api/auth/register/", views.api_register, name="api_register"),

    re_path(r"^proxy/(?P<path>.*)$", views.api_proxy, name="api_proxy"),
]