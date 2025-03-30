from django.http import JsonResponse
from ninja import NinjaAPI

api = NinjaAPI(
    csrf=True,
    title="Django WebGIS API",
    description="Endpoints for user authentication, registration, and password management."
)


def generate_response(success: bool, message: str, status: int = 200, **kwargs):
    """Utility function to format JSON responses."""
    return JsonResponse({"success": success, "message": message, **kwargs}, status=status)


# -------------------- USER PROFILE --------------------
@api.get("/user", tags=["User"])
def get_user(request):
    """Retrieve the authenticated user's details."""
    if not request.user.is_authenticated:
        return generate_response(False, "Not authenticated", status=401)

    user_data = {
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
    }
    return generate_response(True, "Authenticated user data", user=user_data)
