from django.urls import path

from .views import (
    DeviceTokenCreateAPIView,
    DeviceTokenDeleteAPIView,
    NotificationDetailAPIView,
    NotificationListAPIView,
    NotificationMarkAllReadAPIView,
    NotificationMarkReadAPIView,
    NotificationSettingsAPIView,
    NotificationUnreadCountAPIView,
)

urlpatterns = [
    # * T-NOTIF-01: Notification list with unread filtering & pagination
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    # * Unread badge count
    path("unread-count/", NotificationUnreadCountAPIView.as_view(), name="notification-unread-count"),
    # * Mark all as read ("تحديد الكل كمقروء")
    path("mark-all-read/", NotificationMarkAllReadAPIView.as_view(), name="notification-mark-all-read"),
    # * T-NOTIF-SETT: Notification settings
    path("settings/", NotificationSettingsAPIView.as_view(), name="notification-settings"),
    # * Device FCM Token registration & unregistration
    path("devices/", DeviceTokenCreateAPIView.as_view(), name="device-token-create"),
    path("devices/unregister/", DeviceTokenDeleteAPIView.as_view(), name="device-token-delete"),
    # * T-NOTIF-02: Notification details & mark-as-read
    path("<uuid:pk>/", NotificationDetailAPIView.as_view(), name="notification-detail"),
    path("<uuid:pk>/read/", NotificationMarkReadAPIView.as_view(), name="notification-mark-read"),
]
