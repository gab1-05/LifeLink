from django.db import models
from django.contrib.auth.models import User


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
    is_verified = models.BooleanField(default=False)
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