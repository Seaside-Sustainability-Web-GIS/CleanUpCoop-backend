from ninja import NinjaAPI
from ninja.security import django_auth
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.http import JsonResponse
from .models import CustomUser as User
from . import schemas

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

api = NinjaAPI(csrf=True)  # Enable CSRF protection


@api.get("/set-csrf-token")
def get_csrf_token(request):
    csrf_token = get_token(request)

    response = JsonResponse({"csrftoken": csrf_token})

    response.set_cookie(
        "csrftoken",
        csrf_token,
        httponly=False,  # ✅ Allows frontend JavaScript to read it
        secure=False,  # ✅ Only enable in production with HTTPS
        samesite="Lax",
    )

    return response


# User login with session authentication
@api.post("/login")
def login_view(request, payload: schemas.SignInSchema):
    user = authenticate(request, email=payload.email, password=payload.password)
    if user is None:
        return JsonResponse({"success": False, "message": "Invalid email or password"}, status=401)

    login(request, user)
    request.session.save()

    response = JsonResponse({
        "success": True,
        "user": {
            "username": user.username,
            "email": user.email
        }
    })

    response["Access-Control-Allow-Credentials"] = "true"
    return response


# Logout and clear session cookies
@api.post("/logout", auth=django_auth)
def logout_view(request):

    logout(request)
    request.session.flush()

    response = JsonResponse({"message": "Logged out successfully"})
    response.delete_cookie("sessionid")
    response.delete_cookie("csrftoken")

    return response


# Get logged-in user details
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


# Register new users safely
@api.post("/register")
def register(request, payload: schemas.SignInSchema):
    user, created = User.objects.get_or_create(username=payload.email, email=payload.email)

    if not created:
        return {"error": "User already exists"}

    user.set_password(payload.password)
    user.save()

    return {"success": "User registered successfully"}


# Forgot Password endpoint
@api.post("/forgot-password")
def forgot_password(request, payload: schemas.ForgotPasswordSchema):
    try:
        user = User.objects.get(email=payload.email)
    except User.DoesNotExist:
        return JsonResponse({"message": "If the email is registered, a password reset email has been sent."})

    # Generate a secure token and encode the user's primary key.
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Build the reset password URL.
    reset_link = f"http://localhost:8000/api/reset-password?uid={uid}&token={token}"

    # Send the password reset email (ensure your email backend is configured).
    send_mail(
        subject="Password Reset Request",
        message=f"Click the following link to reset your password:\n\n{reset_link}",
        from_email="noreply@example.com",
        recipient_list=[user.email],
        fail_silently=False,
    )

    return JsonResponse({"message": "If the email is registered, a password reset email has been sent."})


# ✅ Reset Password endpoint
@api.post("/reset-password")
def reset_password(request, payload: schemas.ResetPasswordSchema):
    try:
        # Decode the uid to retrieve the user's primary key.
        uid = force_str(urlsafe_base64_decode(payload.uid))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({"error": "Invalid uid"}, status=400)

    # Validate the token.
    if not default_token_generator.check_token(user, payload.token):
        return JsonResponse({"error": "Invalid or expired token"}, status=400)

    # Update the user's password.
    user.set_password(payload.new_password)
    user.save()

    return JsonResponse({"message": "Password reset successfully."})
