from ninja import NinjaAPI
from ninja.security import django_auth
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.http import JsonResponse
from .models import CustomUser as User
from . import schemas

api = NinjaAPI(csrf=True)  # Enable CSRF protection


@api.get("/set-csrf-token")
def get_csrf_token(request):
    csrf_token = get_token(request)  # ✅ Get the CSRF token

    print("DEBUG: Issued CSRF Token =", csrf_token)
    print("DEBUG: CSRF Token from Cookie (before setting) =", request.COOKIES.get("csrftoken"))

    response = JsonResponse({"csrftoken": csrf_token})

    # ✅ Ensure CSRF token in cookie matches the JSON response
    response.set_cookie(
        "csrftoken",
        csrf_token,
        httponly=False,  # ✅ Allows frontend JavaScript to read it
        secure=False,  # ✅ Only enable in production with HTTPS
        samesite="Lax",
    )

    print("DEBUG: CSRF Token from Cookie (after setting) =", response.cookies["csrftoken"].value)

    return response


# ✅ User login with session authentication
@api.post("/login")
def login_view(request, payload: schemas.SignInSchema):
    user = authenticate(request, email=payload.email, password=payload.password)
    if user is None:
        return JsonResponse({"success": False, "message": "Invalid email or password"}, status=401)

    login(request, user)
    request.session.save()  # ✅ Ensure session is saved

    print("DEBUG: Session Key =", request.session.session_key)

    return JsonResponse({
        "success": True,
        "user": {
            "username": user.username,
            "email": user.email
        }
    })


# ✅ Logout and clear session cookies
@api.post("/logout", auth=django_auth)
def logout_view(request):
    print("DEBUG: request.auth =", request.auth)
    print("DEBUG: sessionid =", request.COOKIES.get("sessionid"))

    if request.auth:
        logout(request)
        request.session.flush()  # ✅ Ensures all session data is cleared

        response = JsonResponse({"message": "Logged out successfully"})
        response.delete_cookie("sessionid")  # ✅ Clears session cookie
        response.delete_cookie("csrftoken")  # ✅ Clears CSRF token

        print("DEBUG: User logged out successfully")
        return response

    print("DEBUG: Logout failed - Unauthorized")
    return JsonResponse({"detail": "Unauthorized"}, status=401)


# ✅ Get logged-in user details
@api.get("/user", auth=django_auth)
def user(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    secret_fact = (
        "The moment one gives close attention to any thing, even a blade of grass",
        "it becomes a mysterious, awesome, indescribably magnificent world in itself."
    )
    return {
        "username": request.user.username,
        "email": request.user.email,
        "secret_fact": secret_fact
    }


# ✅ Register new users safely
@api.post("/register")
def register(request, payload: schemas.SignInSchema):
    user, created = User.objects.get_or_create(username=payload.email, email=payload.email)

    if not created:
        return {"error": "User already exists"}

    user.set_password(payload.password)
    user.save()

    return {"success": "User registered successfully"}
