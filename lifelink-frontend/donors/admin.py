from django.contrib import admin
from .models import (
    UserProfile,
    DonorProfile,
    HospitalProfile,
    BloodRequest,
    DonorMatch,
    Message,
    Notification,
    DonationHistory,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "phone", "is_verified", "created_at")
    list_filter = ("user_type", "is_verified")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "blood_type", "availability_status", "is_active", "created_at")
    list_filter = ("blood_type", "availability_status", "is_active")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = ("hospital_name", "registration_number", "phone_emergency", "created_at")
    search_fields = ("hospital_name", "registration_number", "user__email")


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_name", "required_blood_type", "urgency", "status", "hospital", "created_at")
    list_filter = ("status", "urgency", "required_blood_type")
    search_fields = ("patient_name", "hospital__hospital_name")
    readonly_fields = ("created_at", "request_date")
    fieldsets = (
        ("Request Information", {
            "fields": ("hospital", "patient_name", "required_blood_type", "quantity")
        }),
        ("Location & Time", {
            "fields": ("latitude", "longitude", "deadline", "created_at", "request_date")
        }),
        ("Status", {
            "fields": ("urgency", "status")
        }),
    )


@admin.register(DonorMatch)
class DonorMatchAdmin(admin.ModelAdmin):
    list_display = ("id", "blood_request", "donor", "match_score", "distance_km", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("donor__user__username", "blood_request__patient_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("sender__username", "receiver__username", "content")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("user__username", "title", "message")


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "donor", "blood_request", "quantity_donated", "status", "donation_date", "created_at")
    list_filter = ("status",)
    search_fields = ("donor__user__username", "blood_request__patient_name")