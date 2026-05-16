import json
import random
import math
import logging
import os
import hmac
import hashlib
import secrets
from datetime import datetime
from datetime import date, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect, csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.core.mail import get_connection, EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)

def parse_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8")), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"error": "Invalid JSON body"}, status=400)

def frontend_to_blood_type(value, default="O+"):
    if not value:
        return default
    return value.replace("_POSITIVE", "+").replace("_NEGATIVE", "-")

def blood_type_to_frontend(value):
    return value.replace("+", "_POSITIVE").replace("-", "_NEGATIVE") if value else "O_POSITIVE"

def frontend_to_urgency(value):
    mapped = {
        "CRITICAL": "critical",
        "URGENT": "high",
        "HIGH": "high",
        "NORMAL": "medium",
        "MEDIUM": "medium",
        "LOW": "low",
    }
    return mapped.get((value or "").upper(), "high")

def urgency_to_frontend(value):
    mapped = {
        "critical": "CRITICAL",
        "high": "URGENT",
        "medium": "NORMAL",
        "low": "NORMAL",
    }
    return mapped.get(value, "NORMAL")

def status_to_frontend(value):
    mapped = {
        "pending": "OPEN",
        "matched": "MATCHED",
        "completed": "FULFILLED",
        "cancelled": "CANCELLED",
    }
    return mapped.get(value, "OPEN")

def request_to_json(r, viewer=None):
    owner = r.created_by or r.hospital.user
    viewer_id = getattr(viewer, "id", None)
    owner_ids = {r.hospital.user_id}
    if r.created_by_id:
        owner_ids.add(r.created_by_id)
    can_manage = bool(viewer_id and viewer_id in owner_ids)
    return {
        "id": r.id,
        "hospitalName": r.hospital.hospital_name,
        "hospitalAddress": r.hospital.address,
        "bloodType": blood_type_to_frontend(r.required_blood_type),
        "urgency": urgency_to_frontend(r.urgency),
        "unitsNeeded": r.quantity,
        "contactPhone": r.hospital.phone_emergency,
        "latitude": float(r.latitude) if r.latitude else None,
        "longitude": float(r.longitude) if r.longitude else None,
        "status": status_to_frontend(r.status),
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "description": "",
        "canManage": can_manage,
        "canFulfill": can_manage and r.status in ["pending", "matched"],
        "canDelete": can_manage and r.status in ["pending", "matched"],
        "createdById": r.created_by_id,
        "hospitalUserId": r.hospital.user_id,
        "patient": {
            "id": owner.id if owner else None,
            "fullName": owner.get_full_name() or owner.username if owner else r.patient_name,
        },
    }

def split_full_name(full_name):
    parts = (full_name or "").strip().split(" ", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ((parts[0] if parts else ""), "")

def resolve_login_username(identifier):
    identifier = (identifier or "").strip()
    if not identifier:
        return None
    user = User.objects.filter(
        Q(username__iexact=identifier) | Q(email__iexact=identifier)
    ).first()
    return user.username if user else identifier

def ensure_user_profile(user):
    from .models import UserProfile
    phone = f"user-{user.id}"
    return UserProfile.objects.get_or_create(
        user=user,
        defaults={"phone": phone, "user_type": "donor", "is_verified": True},
    )

def donor_defaults():
    return {
        "blood_type": "O+",
        "date_of_birth": date(1995, 1, 1),
        "gender": "O",
        "address": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "total_donations": 0,
        "rating_total": 0,
        "rating_count": 0,
        "availability_status": True,
        "is_active": True,
    }

def donor_rating(donor):
    if not donor or not donor.rating_count:
        return None
    return round(donor.rating_total / donor.rating_count, 2)

def notify_compatible_donors(req):
    from .models import DonorProfile, Notification
    donors = DonorProfile.objects.filter(
        is_active=True,
        availability_status=True,
        blood_type=req.required_blood_type,
    ).exclude(user=req.created_by).select_related("user", "user__userprofile")
    message = f"{req.required_blood_type} needed at {req.hospital.hospital_name}."
    notifications = [
        Notification(
            user=donor.user,
            title="New Blood Request Nearby",
            message=message,
            notification_type="request",
        )
        for donor in donors
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)
    recipients = [
        donor.user.email
        for donor in donors
        if donor.user.email and getattr(getattr(donor.user, "userprofile", None), "email_notifications", True)
    ]
    if recipients:
        try:
            send_mail(
                "LifeLink blood request near you",
                message,
                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.local"),
                recipients,
                fail_silently=False,
            )
            logger.info("Request %s email alerts sent to %s recipients", req.id, len(recipients))
        except Exception:
            logger.exception("Failed to send request %s email alerts", req.id)

def build_user_data(user):
    if not user.is_authenticated:
        return {"is_authenticated": False}
    
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "fullName": user.get_full_name() or user.username,
        "is_authenticated": True,
    }
    
    try:
        from .models import UserProfile, DonorProfile
        up, _ = ensure_user_profile(user)
        data["role"] = up.user_type.upper()
        data["phone"] = up.phone
        data["emailNotifications"] = up.email_notifications
        
        if up.user_type == "donor":
            dp, _ = DonorProfile.objects.get_or_create(user=user, defaults=donor_defaults())
            data["bloodType"] = blood_type_to_frontend(dp.blood_type)
            data["isAvailable"] = dp.availability_status
            data["city"] = dp.address
            data["latitude"] = float(dp.latitude) if dp.latitude else None
            data["longitude"] = float(dp.longitude) if dp.longitude else None
            data["totalDonations"] = dp.total_donations
            data["rating"] = donor_rating(dp)
            data["ratingCount"] = dp.rating_count
            if dp.last_donation_date:
                data["lastDonationDate"] = dp.last_donation_date.isoformat()
                data["nextEligibleDate"] = (dp.last_donation_date + timedelta(days=90)).isoformat()
    except Exception:
        pass
        
    return data

def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "index.html")

def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "auth/login.html")

@ensure_csrf_cookie
def forgot_password_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "auth/forgot_password.html")

def register_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "auth/register.html")

@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard(request):
    user_data = build_user_data(request.user)
    return render(request, "donors/dashboard.html", {"user": json.dumps(user_data)})

@login_required(login_url="login")
@ensure_csrf_cookie
def map_view(request):
    user_data = build_user_data(request.user)
    return render(request, "dashboard/map.html", {"user": json.dumps(user_data)})

@login_required(login_url="login")
@ensure_csrf_cookie
def requests_page(request):
    user_data = build_user_data(request.user)
    return render(request, "dashboard/requests.html", {"user": json.dumps(user_data)})

@login_required(login_url="login")
@ensure_csrf_cookie
def messages_page(request):
    user_data = build_user_data(request.user)
    return render(request, "dashboard/messages.html", {"user": json.dumps(user_data)})

@login_required(login_url="login")
@ensure_csrf_cookie
def profile_page(request):
    user_data = build_user_data(request.user)
    return render(request, "dashboard/profile.html", {"user": json.dumps(user_data)})

@login_required(login_url="login")
@ensure_csrf_cookie
def donors_page(request):
    user_data = build_user_data(request.user)
    return render(request, "dashboard/donors.html", {"user": json.dumps(user_data)})

def logout_view(request):
    logout(request)
    return redirect("login")

# API ENDPOINTS
@csrf_protect
@require_http_methods(["POST"])
def api_login(request):
    data, err = parse_json_body(request)
    if err:
        return err

    identifier = data.get("username") or data.get("email")
    username = resolve_login_username(identifier)
    password = data.get("password")
    now = timezone.now()

    maybe_user = User.objects.filter(
        Q(username__iexact=(identifier or "").strip()) | Q(email__iexact=(identifier or "").strip())
    ).first()

    if maybe_user:
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=maybe_user).first()
        if profile and profile.lockout_until and profile.lockout_until > now:
            return JsonResponse(
                {"error": "This account is temporarily locked. Please try again later."},
                status=403,
            )

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile and (profile.failed_login_attempts or profile.lockout_until):
            profile.failed_login_attempts = 0
            profile.lockout_until = None
            profile.save(update_fields=["failed_login_attempts", "lockout_until"])
        return JsonResponse({
            "success": True,
            "redirect": "/dashboard/",
            "user": build_user_data(user),
        })

    if maybe_user:
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=maybe_user).first()
        if profile:
            profile.failed_login_attempts += 1
            if profile.failed_login_attempts >= 5:
                profile.lockout_until = now + timedelta(minutes=15)
                profile.failed_login_attempts = 0
            profile.save(update_fields=["failed_login_attempts", "lockout_until"])

    exists = User.objects.filter(
        Q(username__iexact=(identifier or "").strip()) | Q(email__iexact=(identifier or "").strip())
    ).exists()
    if not exists:
        return JsonResponse(
            {"error": "No account was found for that username or email. If this was created before the sample reseed, please register it again."},
            status=404,
        )
    return JsonResponse({"error": "Password is incorrect for that account."}, status=401)

@csrf_protect
@require_http_methods(["POST"])
def api_register(request):
    if request.method == "POST":
        data, err = parse_json_body(request)
        if err: return err
        from .models import UserProfile, DonorProfile
        
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("fullName", "")
        user_type = data.get("role", "DONOR").lower() # Match frontend payload 'role'
        phone = data.get("phone") or f"pending-{random.randint(100000, 999999)}"
        
        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            return JsonResponse({"error": "User already exists"}, status=400)
            
        user = User.objects.create_user(username=email, email=email, password=password)
        if " " in full_name:
            user.first_name, user.last_name = full_name.split(" ", 1)
        else:
            user.first_name = full_name
        user.save()
        
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            email_notifications=bool(data.get("emailNotifications", True)),
        )
        if user_type == "donor":
            DonorProfile.objects.create(
                user=user, 
                address=data.get("city", ""),
                blood_type=frontend_to_blood_type(data.get("bloodType")),
                date_of_birth=date(1995, 1, 1),
                gender=data.get("gender", "O")[:1].upper() if data.get("gender") else "O",
                latitude=data.get("latitude"),
                longitude=data.get("longitude")
            )
            
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({
            "success": True, 
            "redirect": "/dashboard/",
            "user": build_user_data(user)
        })
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_protect
@require_http_methods(["POST"])
def api_send_password_reset_otp(request):
    data, err = parse_json_body(request)
    if err:
        return err

    email = (data.get("email") or "").strip()
    if not email:
        return JsonResponse({"error": "Please provide your email address."}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if user:
        from .models import PasswordResetOTP
        now = timezone.now()
        recent_window = now - timedelta(hours=1)
        recent_count = PasswordResetOTP.objects.filter(user=user, created_at__gte=recent_window).count()
        if recent_count >= 5:
            return JsonResponse({"error": "Too many recovery requests. Please try again later."}, status=429)

        otp = "".join(secrets.choice("0123456789") for _ in range(6))
        PasswordResetOTP.objects.create(
            user=user,
            otp_hash=hashlib.sha256(otp.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(minutes=15),
        )
        try:
            send_mail(
                "LifeLink password recovery code",
                f"Your recovery code is: {otp}\n\nThis code expires in 15 minutes.",
                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.local"),
                [user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send password reset OTP for user %s", user.id)

    return JsonResponse({
        "success": True,
        "message": "If an account exists for that email, a recovery code has been sent.",
    })

@csrf_protect
@require_http_methods(["POST"])
def api_reset_password_with_otp(request):
    data, err = parse_json_body(request)
    if err:
        return err

    email = (data.get("email") or "").strip()
    otp = (data.get("otp") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirmPassword") or ""

    if not email or not otp or not password or not confirm_password:
        return JsonResponse({"error": "Email, code, and both password fields are required."}, status=400)
    if password != confirm_password:
        return JsonResponse({"error": "Passwords do not match."}, status=400)
    if len(password) < 8:
        return JsonResponse({"error": "Password must be at least 8 characters long."}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return JsonResponse({"error": "Invalid recovery code or email."}, status=400)

    from .models import PasswordResetOTP
    otp_entry = PasswordResetOTP.objects.filter(
        user=user,
        is_used=False,
        expires_at__gte=timezone.now(),
    ).order_by("-created_at").first()

    if not otp_entry:
        return JsonResponse({"error": "Invalid or expired recovery code."}, status=400)

    if otp_entry.attempt_count >= 5:
        otp_entry.is_used = True
        otp_entry.save(update_fields=["is_used"])
        return JsonResponse({"error": "This recovery code is locked due to too many incorrect attempts."}, status=403)

    otp_hash = hashlib.sha256(otp.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(otp_hash, otp_entry.otp_hash):
        otp_entry.attempt_count += 1
        if otp_entry.attempt_count >= 5:
            otp_entry.is_used = True
        otp_entry.save(update_fields=["attempt_count", "is_used"])
        return JsonResponse({"error": "Invalid or expired recovery code."}, status=400)

    otp_entry.is_used = True
    otp_entry.save(update_fields=["is_used"])
    user.set_password(password)
    user.save()

    return JsonResponse({"success": True, "message": "Password has been reset successfully."})

def api_requests_stats(request):
    from .models import DonorProfile, BloodRequest
    return JsonResponse({
        "totalDonors": DonorProfile.objects.count(),
        "availableDonors": DonorProfile.objects.filter(availability_status=True).count(),
        "openRequests": BloodRequest.objects.filter(status__in=["pending", "matched"]).count(),
        "fulfilledRequests": BloodRequest.objects.filter(status="completed").count(),
    })

@login_required
def api_requests(request):
    from .models import BloodRequest, HospitalProfile, UserProfile
    if request.method == "GET":
        try:
            lat = request.GET.get("lat")
            lng = request.GET.get("lng")
            radius_str = request.GET.get("radius", "50").rstrip("/")
            radius = float(radius_str) if radius_str else 50.0
        except (ValueError, TypeError):
            radius = 50.0

        blood_type = request.GET.get("bloodType")

        reqs = BloodRequest.objects.filter(status__in=["pending", "matched"])
        if blood_type:
            mapped_bt = blood_type.replace("_POSITIVE", "+").replace("_NEGATIVE", "-")
            reqs = reqs.filter(required_blood_type=mapped_bt)

        data = []
        for r in reqs:
            if lat and lng and r.latitude and r.longitude:
                d = math.sqrt((float(r.latitude) - float(lat))**2 + (float(r.longitude) - float(lng))**2) * 111
                if d > radius: continue
            data.append(request_to_json(r, request.user))
        return JsonResponse(data, safe=False)
    if request.method == "POST":
        data, err = parse_json_body(request)
        if err: return err
        hospital_name = data.get("hospitalName") or "LifeLink Partner Hospital"
        phone = data.get("contactPhone") or "9999999999"
        lat = data.get("latitude") or 19.0760
        lng = data.get("longitude") or 72.8777
        hospital = None
        try:
            up, _ = ensure_user_profile(request.user)
            if up.user_type == "hospital":
                hospital = HospitalProfile.objects.filter(user=request.user).first()
        except Exception:
            hospital = None
        if hospital is None:
            hospital_user, _ = User.objects.get_or_create(
                username=f"hospital-{request.user.id}@lifelink.local",
                defaults={"email": f"hospital-{request.user.id}@lifelink.local", "first_name": hospital_name},
            )
            UserProfile.objects.get_or_create(
                user=hospital_user,
                defaults={"phone": f"hosp-{request.user.id}", "user_type": "hospital", "is_verified": True},
            )
            hospital, _ = HospitalProfile.objects.get_or_create(
                user=hospital_user,
                defaults={
                    "hospital_name": hospital_name,
                    "registration_number": f"LOCAL-{request.user.id}",
                    "latitude": lat,
                    "longitude": lng,
                    "address": data.get("hospitalAddress") or "Mumbai",
                    "phone_emergency": phone,
                },
            )
        req = BloodRequest.objects.create(
            hospital=hospital,
            created_by=request.user,
            patient_name=data.get("patientName") or "Emergency Patient",
            required_blood_type=frontend_to_blood_type(data.get("bloodType")),
            quantity=int(data.get("unitsNeeded") or 1),
            urgency=frontend_to_urgency(data.get("urgency")),
            latitude=lat,
            longitude=lng,
            deadline=None,
        )
        notify_compatible_donors(req)
        # Confirmation email to requester if enabled on profile.
        if request.user.email:
            try:
                requester_profile = getattr(request.user, "userprofile", None)
                if requester_profile is None or requester_profile.email_notifications:
                    send_mail(
                        "LifeLink request posted",
                        f"Your {req.required_blood_type} request at {req.hospital.hospital_name} was posted successfully.",
                        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.local"),
                        [request.user.email],
                        fail_silently=False,
                    )
            except Exception:
                logger.exception("Failed to send requester confirmation email for request %s", req.id)
        if req.created_by_id:
            from .models import Notification
            Notification.objects.create(
                user=request.user,
                title="Request Posted",
                message=f"Your {req.required_blood_type} request is now visible to donors.",
                notification_type="request",
            )
        return JsonResponse({"success": True, "id": req.id, "message": "Blood request posted and visible on the map."}, status=201)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@login_required
def api_users_donors(request):
    from .models import DonorProfile
    try:
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius_str = request.GET.get("radius", "50").rstrip("/")
        radius = float(radius_str) if radius_str else 50.0
    except (ValueError, TypeError):
        radius = 50.0
    
    blood_type = request.GET.get("bloodType")
    search_q = request.GET.get("q")
    sort_by = request.GET.get("sortBy", "distance")


    donors = DonorProfile.objects.filter(is_active=True).select_related("user")
    if blood_type:
        mapped_bt = blood_type.replace("_POSITIVE", "+").replace("_NEGATIVE", "-")
        donors = donors.filter(blood_type=mapped_bt)
    if search_q:
        donors = donors.filter(user__first_name__icontains=search_q) | donors.filter(address__icontains=search_q)
    if request.GET.get("isAvailable") in ["true", "false"]:
        donors = donors.filter(availability_status=request.GET.get("isAvailable") == "true")

    data = []
    for d in donors:
        dist = None
        if lat and lng and d.latitude and d.longitude:
            dist = math.sqrt((float(d.latitude) - float(lat))**2 + (float(d.longitude) - float(lng))**2) * 111
            if dist > radius: continue
        data.append({
            "id": d.user.id,
            "fullName": d.user.get_full_name() or d.user.username,
            "city": d.address or "Unknown",
            "bloodType": blood_type_to_frontend(d.blood_type),
            "isAvailable": d.availability_status,
            "latitude": float(d.latitude) if d.latitude else None,
            "longitude": float(d.longitude) if d.longitude else None,
            "distance": dist,
            "totalDonations": d.total_donations,
            "rating": donor_rating(d),
            "ratingCount": d.rating_count,
            "nextEligibleDate": (d.last_donation_date + timedelta(days=90)).isoformat() if d.last_donation_date else None,
        })
    if sort_by == "distance": data.sort(key=lambda x: x["distance"] or 999)
    elif sort_by == "rating": data.sort(key=lambda x: x["rating"] or 0, reverse=True)
    elif sort_by == "donations": data.sort(key=lambda x: x["totalDonations"] or 0, reverse=True)
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
def api_toggle_availability(request):
    from .models import DonorProfile
    try:
        profile = DonorProfile.objects.get(user=request.user)
        profile.availability_status = not profile.availability_status
        profile.save()
        return JsonResponse({"isAvailable": profile.availability_status})
    except DonorProfile.DoesNotExist:
        return JsonResponse({"error": "Donor profile not found"}, status=404)

@login_required
def api_notifications_unread_count(request):
    from .models import Notification
    return JsonResponse({"count": Notification.objects.filter(user=request.user, is_read=False).count()})

@login_required
def api_messages_unread_count(request):
    from .models import Message
    return JsonResponse({"count": Message.objects.filter(receiver=request.user, is_read=False).count()})

@login_required
def api_notifications(request):
    from .models import Notification
    notifs = Notification.objects.filter(user=request.user).order_by("-created_at")[:20]
    data = [{"id": n.id, "title": n.title, "message": n.message, "type": n.notification_type.upper() if n.notification_type else "SYSTEM", "isRead": n.is_read, "createdAt": n.created_at.isoformat()} for n in notifs]
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
def api_notifications_read(request, notif_id):
    from .models import Notification
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({"success": True})

@login_required
@csrf_exempt
def api_notifications_read_all(request):
    from .models import Notification
    Notification.objects.filter(user=request.user).update(is_read=True)
    return JsonResponse({"success": True})

@login_required
@csrf_exempt
def api_notifications_delete(request, notif_id):
    if request.method not in ["DELETE", "POST"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    from .models import Notification
    deleted, _ = Notification.objects.filter(id=notif_id, user=request.user).delete()
    if not deleted:
        return JsonResponse({"error": "Notification not found"}, status=404)
    return JsonResponse({"success": True})

@login_required
@csrf_exempt
def api_delete_request(request, request_id):
    if request.method not in ["DELETE", "POST"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    from .models import BloodRequest
    try:
        req = BloodRequest.objects.select_related("hospital").get(id=request_id)
    except BloodRequest.DoesNotExist:
        return JsonResponse({"error": "Request not found."}, status=404)

    is_owner = req.created_by_id == request.user.id or req.hospital.user_id == request.user.id
    if not is_owner:
        return JsonResponse({"error": "You can only delete your own request."}, status=403)
    if req.status not in ["pending", "matched"]:
        return JsonResponse({"error": "Only open or matched requests can be deleted."}, status=400)

    req.delete()
    return JsonResponse({"success": True, "message": "Blood request deleted."})

@login_required
@csrf_exempt
def api_test_email(request):
    if request.method not in ["POST", "GET"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    target_email = (request.GET.get("to") or "").strip()
    if not target_email:
        target_email = request.user.email
    if not target_email:
        return JsonResponse({"error": "Your account does not have an email address."}, status=400)
    debug = {
        "pid": os.getpid(),
        "server_time": datetime.utcnow().isoformat() + "Z",
        "backend": getattr(settings, "EMAIL_BACKEND", ""),
        "host": getattr(settings, "EMAIL_HOST", ""),
        "port": getattr(settings, "EMAIL_PORT", ""),
        "tls": bool(getattr(settings, "EMAIL_USE_TLS", False)),
        "ssl": bool(getattr(settings, "EMAIL_USE_SSL", False)),
        "user_set": bool(getattr(settings, "EMAIL_HOST_USER", "")),
        "pass_set": bool(getattr(settings, "EMAIL_HOST_PASSWORD", "")),
        "from_email": getattr(settings, "DEFAULT_FROM_EMAIL", ""),
    }
    try:
        connection = get_connection(
            backend=getattr(settings, "EMAIL_BACKEND", None),
            host=getattr(settings, "EMAIL_HOST", ""),
            port=getattr(settings, "EMAIL_PORT", 587),
            username=getattr(settings, "EMAIL_HOST_USER", ""),
            password=getattr(settings, "EMAIL_HOST_PASSWORD", ""),
            use_tls=getattr(settings, "EMAIL_USE_TLS", True),
            use_ssl=getattr(settings, "EMAIL_USE_SSL", False),
            fail_silently=False,
        )
        msg = EmailMessage(
            subject="LifeLink email test",
            body="This is a test email from LifeLink. SMTP is configured and working.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.local"),
            to=[target_email],
            connection=connection,
        )
        sent = msg.send(fail_silently=False)
        return JsonResponse({
            "success": True,
            "message": f"Test email sent to {target_email}",
            "sent_count": sent,
            "debug": debug,
        })
    except Exception as exc:
        logger.exception("api_test_email failed")
        return JsonResponse({"error": f"Email send failed: {exc}", "debug": debug}, status=500)

@login_required
def api_users_me(request):
    if request.method == "GET":
        return JsonResponse(build_user_data(request.user))
    if request.method in ["PUT", "PATCH"]:
        from .models import DonorProfile
        data, err = parse_json_body(request)
        if err: return err
        full_name = data.get("fullName")
        if full_name is not None:
            request.user.first_name, request.user.last_name = split_full_name(full_name)
            request.user.save(update_fields=["first_name", "last_name"])
        up, _ = ensure_user_profile(request.user)
        if data.get("phone") is not None:
            up.phone = data.get("phone") or f"user-{request.user.id}"
        if data.get("emailNotifications") is not None:
            up.email_notifications = bool(data.get("emailNotifications"))
        up.save(update_fields=["phone", "email_notifications", "updated_at"])
        if up.user_type == "donor":
            dp, _ = DonorProfile.objects.get_or_create(user=request.user, defaults=donor_defaults())
            if data.get("bloodType"):
                dp.blood_type = frontend_to_blood_type(data.get("bloodType"))
            if data.get("city") is not None:
                dp.address = data.get("city") or ""
            if data.get("latitude") is not None:
                dp.latitude = data.get("latitude")
            if data.get("longitude") is not None:
                dp.longitude = data.get("longitude")
            dp.save()
        return JsonResponse({"success": True, "user": build_user_data(request.user)})
    return JsonResponse({"error": "Method not allowed"}, status=405)

@login_required
@csrf_exempt
def api_messages(request):
    from .models import Message, Notification
    if request.method == "POST":
        data, err = parse_json_body(request)
        if err: return err
        receiver = User.objects.get(id=data["receiverId"])
        text = data.get("text") or data.get("content") or ""
        if not text.strip():
            return JsonResponse({"error": "Message text is required"}, status=400)
        Message.objects.create(sender=request.user, receiver=receiver, content=text.strip())
        Notification.objects.create(user=receiver, title="New Message", message=f"From {request.user.get_full_name()}", notification_type="message")
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Method not allowed"}, status=405)

@login_required
def api_requests_my(request):
    from .models import BloodRequest
    reqs = BloodRequest.objects.filter(
        Q(created_by=request.user) | Q(donormatch__donor__user=request.user)
    ).distinct().select_related("hospital", "created_by", "hospital__user")
    data = [request_to_json(r, request.user) for r in reqs]
    return JsonResponse(data, safe=False)

@login_required
def api_messages_conversations(request):
    from .models import Message
    from django.db.models import Q
    msgs = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by("-created_at")
    convos = {}
    for m in msgs:
        other = m.receiver if m.sender == request.user else m.sender
        if other.id not in convos:
            donor = getattr(other, "donorprofile", None)
            name = other.get_full_name() or other.username
            convos[other.id] = {
                "userId": other.id,
                "name": name,
                "userName": name,
                "bloodType": blood_type_to_frontend(donor.blood_type) if donor else "",
                "lastMessage": m.content,
                "time": m.created_at.strftime("%I:%M %p"),
                "unread": 1 if m.receiver == request.user and not m.is_read else 0,
            }
        elif m.receiver == request.user and not m.is_read:
            convos[other.id]["unread"] += 1
    return JsonResponse(list(convos.values()), safe=False)

@login_required
def api_messages_conversation(request, user_id):
    from .models import Message
    from django.db.models import Q
    msgs = Message.objects.filter((Q(sender=request.user) & Q(receiver_id=user_id)) | (Q(sender_id=user_id) & Q(receiver=request.user))).order_by("created_at")
    Message.objects.filter(sender_id=user_id, receiver=request.user, is_read=False).update(is_read=True)
    data = [{"id": m.id, "text": m.content, "senderId": m.sender.id, "time": m.created_at.strftime("%I:%M %p"), "sentAt": m.created_at.isoformat()} for m in msgs]
    return JsonResponse(data, safe=False)

@login_required
def api_live_feed(request):
    activities = [
        {"text": "New blood request from St. Jude Hospital", "time": "2 mins ago", "icon": "🆘"},
        {"text": "Aarav Sharma just registered as a donor", "time": "15 mins ago", "icon": "👤"},
        {"text": "Lifecare Medical Center fulfilled a request", "time": "1 hour ago", "icon": "✅"},
        {"text": "Urgent O- blood needed in Sion", "time": "3 hours ago", "icon": "🚨"}
    ]
    return JsonResponse(activities, safe=False)

@login_required
def api_hospitals(request):
    from .models import HospitalProfile, BloodRequest
    hospitals = HospitalProfile.objects.all()
    data = []
    for h in hospitals:
        active_count = BloodRequest.objects.filter(hospital=h, status="pending").count()
        data.append({
            "id": h.id,
            "name": h.hospital_name,
            "address": h.address,
            "phone": h.phone_emergency,
            "latitude": float(h.latitude) if h.latitude else None,
            "longitude": float(h.longitude) if h.longitude else None,
            "activeRequests": active_count,
            "rating": 4.0 + (h.id % 10) / 10.0 # Mock rating
        })
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
def api_respond_to_request(request, request_id):
    from .models import BloodRequest, DonorProfile, DonorMatch, Notification
    if request.method not in ["PATCH", "POST"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        req = BloodRequest.objects.get(id=request_id)
        donor, _ = DonorProfile.objects.get_or_create(user=request.user, defaults=donor_defaults())
        DonorMatch.objects.get_or_create(
            blood_request=req,
            donor=donor,
            defaults={"match_score": 90, "status": "accepted"},
        )
        req.status = "matched"
        req.save(update_fields=["status"])
        Notification.objects.create(
            user=req.hospital.user,
            title="Donor Response",
            message=f"{request.user.get_full_name() or request.user.username} responded to your request.",
            notification_type="match",
        )
        if req.created_by_id and req.created_by_id != req.hospital.user_id:
            Notification.objects.create(
                user=req.created_by,
                title="Donor Matched",
                message=f"{request.user.get_full_name() or request.user.username} responded to your blood request.",
                notification_type="match",
            )
        return JsonResponse({"success": True, "message": "Thanks. The hospital has been notified."})
    except BloodRequest.DoesNotExist:
        return JsonResponse({"error": "Request not found"}, status=404)

@login_required
@csrf_exempt
def api_fulfill_request(request, request_id):
    from .models import BloodRequest, DonationHistory, Notification
    if request.method not in ["PATCH", "POST"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        req = BloodRequest.objects.get(id=request_id)
        if req.created_by_id and req.created_by_id != request.user.id and req.hospital.user_id != request.user.id:
            return JsonResponse({"error": "You can only fulfill your own request"}, status=403)
        if not req.created_by_id and req.hospital.user_id != request.user.id:
            return JsonResponse({"error": "You can only fulfill your own request"}, status=403)
        if req.status == "completed":
            return JsonResponse({"error": "This request is already fulfilled."}, status=400)
        if req.status == "cancelled":
            return JsonResponse({"error": "Cancelled requests cannot be fulfilled."}, status=400)
        req.status = "completed"
        req.save(update_fields=["status"])
        recipients = {req.hospital.user_id}
        if req.created_by_id:
            recipients.add(req.created_by_id)
        for match in req.donormatch_set.select_related("donor").filter(status__in=["accepted", "completed"]):
            donor = match.donor
            recipients.add(donor.user_id)
            if not DonationHistory.objects.filter(donor=donor, blood_request=req, status="completed").exists():
                donor.total_donations += 1
                donor.last_donation_date = date.today()
                donor.save(update_fields=["total_donations", "last_donation_date"])
                match.status = "completed"
                match.save(update_fields=["status"])
                DonationHistory.objects.create(
                    donor=donor,
                    blood_request=req,
                    quantity_donated=req.quantity,
                    status="completed",
                )
        for user_id in recipients:
            Notification.objects.create(
                user_id=user_id,
                title="Request Fulfilled",
                message=f"The {req.required_blood_type} request at {req.hospital.hospital_name} has been fulfilled.",
                notification_type="match",
            )
        return JsonResponse({"success": True, "message": "Request marked fulfilled."})
    except BloodRequest.DoesNotExist:
        return JsonResponse({"error": "Request not found"}, status=404)

@login_required
@csrf_protect
@require_http_methods(["POST", "PATCH"])
def api_rate_user(request, user_id):
    from .models import DonorProfile, UserRating
    if request.user.id == user_id:
        return JsonResponse({"error": "You cannot rate yourself."}, status=403)

    data, err = parse_json_body(request)
    if err:
        return err

    rating = max(1, min(5, int(data.get("rating") or 5)))
    try:
        donor = DonorProfile.objects.get(user_id=user_id)
    except DonorProfile.DoesNotExist:
        return JsonResponse({"error": "Donor not found"}, status=404)

    existing = UserRating.objects.filter(rater=request.user, rated_user_id=user_id).first()
    if existing:
        return JsonResponse({
            "error": "You have already rated this user. You can only submit one rating.",
            "rating": donor_rating(donor),
            "ratingCount": donor.rating_count,
        }, status=400)

    UserRating.objects.create(rater=request.user, rated_user_id=user_id, rating=rating)
    donor.rating_total += rating
    donor.rating_count += 1
    donor.save(update_fields=["rating_total", "rating_count"])
    return JsonResponse({
        "success": True,
        "rating": donor_rating(donor),
        "ratingCount": donor.rating_count,
    })
