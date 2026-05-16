from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # Auth pages
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password_page, name="forgot_password"),

    # Dashboard pages
    path("dashboard/", views.dashboard, name="dashboard"),
    path("map/", views.map_view, name="map"),
    path("requests/", views.requests_page, name="requests"),
    path("messages/", views.messages_page, name="messages"),
    path("profile/", views.profile_page, name="profile"),
    path("donors/", views.donors_page, name="donors"),

    # API endpoints
    path("api/login/", views.api_login, name="api_login"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/forgot-password/send-otp/", views.api_send_password_reset_otp, name="api_send_password_reset_otp"),
    path("api/forgot-password/reset/", views.api_reset_password_with_otp, name="api_reset_password_with_otp"),
    path("api/requests/stats/", views.api_requests_stats, name="api_requests_stats"),
    path("api/requests/my/", views.api_requests_my, name="api_requests_my"),
    path("api/requests/", views.api_requests, name="api_requests"),
    path("api/users/me/", views.api_users_me, name="api_users_me"),
    path("api/users/donors/", views.api_users_donors, name="api_users_donors"),
    path("api/users/<int:user_id>/rate/", views.api_rate_user, name="api_rate_user"),
    path("api/users/toggle-availability/", views.api_toggle_availability, name="api_toggle_availability"),
    path("api/notifications/unread-count/", views.api_notifications_unread_count, name="api_notif_unread"),
    path("api/messages/unread-count/", views.api_messages_unread_count, name="api_msg_unread"),
    path("api/notifications/", views.api_notifications, name="api_notifications"),
    path("api/notifications/<int:notif_id>/read/", views.api_notifications_read, name="api_notifications_read"),
    path("api/notifications/<int:notif_id>/delete/", views.api_notifications_delete, name="api_notifications_delete"),
    path("api/notifications/read-all/", views.api_notifications_read_all, name="api_notifications_read_all"),
    path("api/requests/<int:request_id>/delete/", views.api_delete_request, name="api_delete_request"),
    path("api/test-email/", views.api_test_email, name="api_test_email"),
    path("api/messages/conversations/", views.api_messages_conversations, name="api_conversations"),
    path("api/messages/conversation/<int:user_id>/", views.api_messages_conversation, name="api_conversation"),
    path("api/messages/", views.api_messages, name="api_messages"),
    path("api/live-feed/", views.api_live_feed, name="api_live_feed"),
    path("api/hospitals/", views.api_hospitals, name="api_hospitals"),
    path("api/requests/<int:request_id>/respond/", views.api_respond_to_request, name="api_respond_to_request"),
    path("api/requests/<int:request_id>/fulfill/", views.api_fulfill_request, name="api_fulfill_request"),
    path("requests/<int:request_id>/respond/", views.api_respond_to_request, name="respond_to_request"),
]
