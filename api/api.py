from django.views.decorators.csrf import csrf_exempt
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

from .schemas import RegisterSchema, LoginSchema

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


@api.post("/login")
def login(request, payload: schemas.LoginSchema):
    try:
        user = User.objects.get(email__iexact=payload.email)
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid email or password"}, status=401)

    if not user.check_password(payload.password):
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
@api.post("/logout")
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

    return {
        "username": request.user.username,
        "email": request.user.email,
    }


# Register new users safely
@api.post("/register")
def register(request, payload: RegisterSchema):
    email = payload.email.lower()

    # Check if user already exists
    user_exists = User.objects.filter(email=email).exists()
    if user_exists:
        return JsonResponse(
            {
                "error": "This email is already registered. Please log in instead or reset your password if needed."
            },
            status=400
        )

    # Create new user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
        }
    )

    user.set_password(payload.password)
    user.save()

    # Send confirmation email
    subject = "Welcome to Our Platform"
    message = f"Hello {payload.first_name},\n\nThank you for registering. Your account has been successfully created."
    from_email = "trash@seasidesustainability.org" #TODO
    recipient_list = [payload.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        return {"success": "User registered successfully, but email could not be sent.", "error": str(e)}

    return {"success": "User registered successfully. A confirmation email has been sent."}


# Forgot Password endpoint
@api.post("/forgot-password")
@csrf_exempt
def forgot_password(request, payload: schemas.ForgotPasswordSchema):
    try:
        user = User.objects.get(email=payload.email)
    except User.DoesNotExist:
        return JsonResponse({"message": "If the email is registered, a password reset email has been sent."})

    # Generate a secure token and encode the user's primary key.
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Build the reset password URL.
    reset_link = f"http://localhost:5713/WebGIS-React/reset-password?uid={uid}&token={token}"

    # Send the password reset email (ensure your email backend is configured).
    send_mail(
        subject="Password Reset Request",
        message=f"Click the following link to reset your password:\n\n{reset_link}",
        from_email="trash@seasidesustainability.org",
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
