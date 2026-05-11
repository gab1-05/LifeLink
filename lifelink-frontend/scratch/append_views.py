
from django.views.decorators.csrf import csrf_exempt

@login_required
def api_requests_stats(request):
    from .models import DonorProfile, BloodRequest
    total_donors = DonorProfile.objects.count()
    available_donors = DonorProfile.objects.filter(availability_status=True).count()
    open_requests = BloodRequest.objects.filter(status="pending").count()
    fulfilled_requests = BloodRequest.objects.filter(status="completed").count()
    
    return JsonResponse({
        "totalDonors": total_donors,
        "availableDonors": available_donors,
        "openRequests": open_requests,
        "fulfilledRequests": fulfilled_requests
    })

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
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def api_messages_unread_count(request):
    from .models import Message
    count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def api_notifications(request):
    from .models import Notification
    notifs = Notification.objects.filter(user=request.user).order_by("-created_at")[:20]
    data = []
    for n in notifs:
        data.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type.upper() if n.notification_type else "SYSTEM",
            "isRead": n.is_read,
            "createdAt": n.created_at.isoformat()
        })
    return JsonResponse(data, safe=False)

@login_required
def api_notifications_read(request, notif_id):
    from .models import Notification
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({"success": True})

@login_required
def api_notifications_read_all(request):
    from .models import Notification
    Notification.objects.filter(user=request.user).update(is_read=True)
    return JsonResponse({"success": True})

@csrf_exempt
def api_login(request):
    if request.method == "POST":
        data, err = parse_json_body(request)
        if err: return err
        username = data.get("username")
        password = data.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({"success": True, "user": build_user_data(user)})
        return JsonResponse({"error": "Invalid credentials"}, status=401)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def api_register(request):
    if request.method == "POST":
        data, err = parse_json_body(request)
        if err: return err
        from django.contrib.auth.models import User
        from .models import UserProfile, DonorProfile
        
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("fullName", "")
        user_type = data.get("userType", "donor")
        
        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "User already exists"}, status=400)
            
        user = User.objects.create_user(username=email, email=email, password=password)
        if " " in full_name:
            user.first_name, user.last_name = full_name.split(" ", 1)
        else:
            user.first_name = full_name
        user.save()
        
        UserProfile.objects.create(user=user, user_type=user_type)
        if user_type == "donor":
            DonorProfile.objects.create(user=user)
            
        login(request, user)
        return JsonResponse({"success": True, "user": build_user_data(user)})
    return JsonResponse({"error": "Method not allowed"}, status=405)
