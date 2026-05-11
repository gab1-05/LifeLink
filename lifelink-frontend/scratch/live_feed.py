
@login_required
def api_live_feed(request):
    activities = [
        {"text": "New blood request from St. Jude Hospital", "time": "2 mins ago", "icon": "🆘"},
        {"text": "Aarav Sharma just registered as a donor", "time": "15 mins ago", "icon": "👤"},
        {"text": "Lifecare Medical Center fulfilled a request", "time": "1 hour ago", "icon": "✅"},
        {"text": "Urgent O- blood needed in Sion", "time": "3 hours ago", "icon": "🚨"}
    ]
    return JsonResponse(activities, safe=False)
