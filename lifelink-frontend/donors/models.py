from django.db import models
from django.contrib.auth.models import User
import hashlib
import json
import logging
import secrets
from django.utils import timezone


BLOOD_TYPE_CHOICES = (
    ("O+", "O Positive"),
    ("O-", "O Negative"),
    ("A+", "A Positive"),
    ("A-", "A Negative"),
    ("B+", "B Positive"),
    ("B-", "B Negative"),
    ("AB+", "AB Positive"),
    ("AB-", "AB Negative"),
)

USER_TYPE_CHOICES = (
    ("donor", "Blood Donor"),
    ("hospital", "Hospital"),
    ("patient", "Patient"),
)

URGENCY_CHOICES = (
    ("critical", "Critical"),
    ("high", "High"),
    ("medium", "Medium"),
    ("low", "Low"),
)

STATUS_CHOICES = (
    ("pending", "Pending"),
    ("matched", "Matched"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email_notifications = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.email} ({self.user_type})"


class DonorProfile(models.Model):
    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    total_donations = models.PositiveIntegerField(default=0)
    rating_total = models.PositiveIntegerField(default=0)
    rating_count = models.PositiveIntegerField(default=0)
    availability_status = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "donor_profiles"
        indexes = [
            models.Index(fields=["blood_type", "is_active"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.blood_type}"


class UserRating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_ratings")
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_ratings")
    rating = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_ratings"
        constraints = [
            models.UniqueConstraint(fields=["rater", "rated_user"], name="unique_user_rating"),
        ]
        indexes = [
            models.Index(fields=["rater", "rated_user"]),
        ]

    def __str__(self):
        return f"Rating {self.rating} from {self.rater.username} to {self.rated_user.username}"


class HospitalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital_name = models.CharField(max_length=150)
    registration_number = models.CharField(max_length=50, unique=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    address = models.CharField(max_length=255)
    phone_emergency = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hospital_profiles"
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return self.hospital_name


class BloodRequest(models.Model):
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_blood_requests")
    patient_name = models.CharField(max_length=100)
    required_blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="high")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    request_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blood_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "urgency"]),
            models.Index(fields=["required_blood_type"]),
        ]

    def __str__(self):
        return f"Request {self.id} - {self.required_blood_type} ({self.urgency})"


class DonorMatch(models.Model):
    MATCH_STATUS = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    )

    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    match_score = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=MATCH_STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "donor_matches"
        ordering = ["-match_score", "-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Match {self.id} - {self.donor.user.get_full_name()}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["receiver", "is_read"]),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("request", "Blood Request"),
        ("match", "Donor Match"),
        ("message", "New Message"),
        ("alert", "Alert"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="alert")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class DonationHistory(models.Model):
    DONATION_STATUS = (
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE)
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    donation_date = models.DateTimeField(null=True, blank=True)
    quantity_donated = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=DONATION_STATUS, default="scheduled")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "donation_history"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Donation - {self.donor.user.get_full_name()}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_hash = models.CharField(max_length=64)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempt_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "password_reset_otps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "otp_hash"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Password reset OTP for {self.user.username} ({'used' if self.is_used else 'pending'})"

    def is_valid(self):
        return not self.is_used and self.expires_at >= timezone.now()

from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=BloodRequest)
def notify_high_priority_request(sender, instance, created, **kwargs):
    if created and instance.urgency in ["critical", "high"]:
        from .services import send_sms_alert
        # For simulation, we assume we find local donors. 
        # In a real app we'd query DonorProfile nearby.
        # This will just print out or execute the sms function.
        msg = f"URGENT: {instance.required_blood_type} blood needed at {instance.hospital.hospital_name}. Patient: {instance.patient_name}."
        # Call the sms function. (It might fail if Twilio isn't configured, but it handles exceptions)
        send_sms_alert("9999999999", msg)
        
        # We also create a notification for hospital 
        Notification.objects.create(
            user=instance.hospital.user,
            title="Urgent Request Created",
            message=msg,
            notification_type="alert"
        )

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserProfile)
def send_registration_welcome(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.create(
        user=instance.user,
        title="Welcome to LifeLink",
        message="Your account has been created successfully.",
        notification_type="alert",
    )
    if instance.user.email:
        try:
            send_mail(
                "Welcome to LifeLink",
                "Your LifeLink account has been created successfully. Thank you for joining us.",
                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.local"),
                [instance.user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send registration welcome email for user %s", instance.user_id)


@receiver(user_logged_in)
def send_login_alert(sender, request, user, **kwargs):
    # De-dupe rapid duplicate login events.
    recent_window = timezone.now() - timedelta(minutes=2)
    if Notification.objects.filter(
        user=user,
        title="Login Successful",
        created_at__gte=recent_window,
    ).exists():
        return

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
    client_ip = (forwarded_for.split(",")[0].strip() if forwarded_for else (request.META.get("REMOTE_ADDR", "unknown") if request else "unknown"))
    login_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    masked_ip = client_ip
    if "." in client_ip:
        parts = client_ip.split(".")
        if len(parts) == 4:
            masked_ip = f"{parts[0]}.{parts[1]}.xxx.xxx"
    elif ":" in client_ip:
        blocks = client_ip.split(":")
        if len(blocks) >= 4:
            masked_ip = ":".join(blocks[:2] + ["xxxx", "xxxx"])

    Notification.objects.create(
        user=user,
        title="Login Successful",
        message=f"Thank you for logging in to LifeLink at {login_time} from {masked_ip}.",
        notification_type="alert",
    )

    recipient = user.email
    if not recipient and request is not None:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            candidate = payload.get("email") or payload.get("username")
            if candidate and "@" in candidate:
                recipient = candidate
        except (ValueError, UnicodeDecodeError):
            recipient = recipient

    if recipient:
        try:
            send_mail(
                "LifeLink login alert",
                f"Thank you for logging in to LifeLink.\n\nTime: {login_time}\nIP Address: {client_ip}",
                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.local"),
                [recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send login email alert for user %s", user.id)
