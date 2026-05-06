import json
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

API = settings.SPRING_API_URL.rstrip("/")


def get_auth_headers(request):
    token = request.session.get("jwt_token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _require_login(request):
    return not request.session.get("jwt_token")


def index(request):
    return render(request, "index.html")


def login_page(request):
    if request.session.get("jwt_token"):
        return redirect("dashboard")
    return render(request, "auth/login.html")


def register_page(request):
    if request.session.get("jwt_token"):
        return redirect("dashboard")
    return render(request, "auth/register.html")


def dashboard(request):
    if _require_login(request):
        return redirect("login")
    return render(request, "dashboard/dashboard.html", {"user": json.dumps(request.session.get("user", {}))})


def map_view(request):
    if _require_login(request):
        return redirect("login")
    return render(request, "dashboard/map.html", {"user": json.dumps(request.session.get("user", {}))})


def requests_page(request):
    if _require_login(request):
        return redirect("login")
    return render(request, "dashboard/requests.html", {"user": json.dumps(request.session.get("user", {}))})


def messages_page(request):
    if _require_login(request):
        return redirect("login")
    return render(request, "dashboard/messages.html", {"user": json.dumps(request.session.get("user", {}))})


def profile_page(request):
    if _require_login(request):
        return redirect("login")
    return render(request, "dashboard/profile.html", {"user": json.dumps(request.session.get("user", {}))})


def donors_page(request):
    if _require_login(request):
        return redirect("login")
    return render(request, "dashboard/donors.html", {"user": json.dumps(request.session.get("user", {}))})


def logout_view(request):
    request.session.flush()
    return redirect("index")


@csrf_exempt
def api_login(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    try:
        resp = requests.post(f"{API}/auth/login", json=data, timeout=10)
        result = resp.json()

        if resp.status_code == 200:
            request.session["jwt_token"] = result.get("token")
            request.session["user"] = result.get("user", {})

        return JsonResponse(result, status=resp.status_code)
    except requests.exceptions.ConnectionError:
        return JsonResponse(
            {"error": "Cannot connect to backend. Is Spring Boot running on port 8080?"},
            status=503,
        )
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Request timed out"}, status=504)


@csrf_exempt
def api_register(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    try:
        resp = requests.post(f"{API}/auth/register", json=data, timeout=10)
        result = resp.json()

        if resp.status_code == 200:
            request.session["jwt_token"] = result.get("token")
            request.session["user"] = result.get("user", {})

        return JsonResponse(result, status=resp.status_code)
    except requests.exceptions.ConnectionError:
        return JsonResponse(
            {"error": "Cannot connect to backend. Is Spring Boot running on port 8080?"},
            status=503,
        )
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Request timed out"}, status=504)


@csrf_exempt
def api_proxy(request, path):
    url = f"{API}/{path}"
    headers = get_auth_headers(request)

    try:
        if request.method == "GET":
            resp = requests.get(url, headers=headers, params=request.GET, timeout=15)
        elif request.method == "POST":
            resp = requests.post(url, headers=headers, data=request.body, timeout=15)
        elif request.method == "PUT":
            resp = requests.put(url, headers=headers, data=request.body, timeout=15)
        elif request.method == "PATCH":
            resp = requests.patch(url, headers=headers, data=request.body, timeout=15)
        elif request.method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=15)
        else:
            return HttpResponseNotAllowed(["GET", "POST", "PUT", "PATCH", "DELETE"])

        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return JsonResponse(resp.json(), status=resp.status_code, safe=False)

        return JsonResponse({"response": resp.text}, status=resp.status_code)

    except requests.exceptions.ConnectionError:
        return JsonResponse(
            {"error": "Backend service unavailable. Ensure Spring Boot is running on port 8080."},
            status=503,
        )
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Request timed out"}, status=504)