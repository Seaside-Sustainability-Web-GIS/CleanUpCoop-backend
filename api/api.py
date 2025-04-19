from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from ninja import NinjaAPI
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from .models import AdoptedArea
from .schemas import AdoptAreaInput, AdoptAreaLayer
from typing import List

User = get_user_model()

api = NinjaAPI(
    csrf=False,
    title="Seaside Sustainability WebGIS API",
    description="Endpoints for user authentication, registration, and password management."
)


# -------------------- Helper: Resolve user from session token --------------------
def get_user_from_token(token):
    try:
        print(f"Looking for session with key: {token}")
        session = Session.objects.get(session_key=token)
        print(f"Session found: {session}")

        session_data = session.get_decoded()
        print(f"Session data: {session_data}")

        user_id = session_data.get('_auth_user_id')
        print(f"User ID from session: {user_id}")

        if not user_id:
            print("No user ID in session")
            return None

        user = User.objects.get(id=user_id)
        print(f"User found: {user}")
        return user
    except Session.DoesNotExist:
        print("Session does not exist")
        return None
    except User.DoesNotExist:
        print("User does not exist")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None


# -------------------- ADOPT AREA --------------------
@api.post("/adopt-area/", tags=["Adopt Area"])
def adopt_area(request, data: AdoptAreaInput):
    session_token = request.headers.get("X-Session-Token")
    user = get_user_from_token(session_token)

    if not user:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)

    try:
        AdoptedArea.objects.create(user=user, **data.model_dump())
        return JsonResponse({"success": True, "message": "Area adopted successfully!"}, status=201)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to save area: {str(e)}"}, status=500)


@api.get("/adopted-area-layer/", response=List[AdoptAreaLayer], tags=["Adopt Area"])
def list_adopted_areas(request):
    return [
        AdoptAreaLayer(
            id=area.id,
            area_name=area.area_name,
            adoptee_name=area.adoptee_name,
            email=area.email,
            lat=area.lat,
            lng=area.lng,
            city=area.city,
            state=area.state,
            country=area.country,
            note=area.note
        )
        for area in AdoptedArea.objects.filter(is_active=True)
    ]


@api.put("/adopt-area/{area_id}/", tags=["Adopt Area"])
def update_adopted_area(request, area_id: int, data: AdoptAreaInput):
    session_token = request.headers.get("X-Session-Token")
    user = get_user_from_token(session_token)

    if not user:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)

    try:
        area = AdoptedArea.objects.get(id=area_id, user=user)
    except AdoptedArea.DoesNotExist:
        return JsonResponse({"success": False, "message": "Adopted area not found"}, status=404)

    for field, value in data.model_dump().items():
        setattr(area, field, value)
    area.save()

    return JsonResponse({"success": True, "message": "Adopted area updated successfully!"})


@api.delete("/adopt-area/{area_id}/", tags=["Adopt Area"])
def delete_adopted_area(request, area_id: int):
    # Get session token from header
    session_token = request.headers.get("X-Session-Token")
    print(f"Received X-Session-Token: {session_token}")

    # Debug the headers to see what's coming through
    print(f"All headers: {dict(request.headers)}")

    user = get_user_from_token(session_token)

    if not user:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)

    try:
        area = AdoptedArea.objects.get(id=area_id, user=user)
        area.delete()
        return JsonResponse({"success": True, "message": "Adopted area deleted successfully!"})
    except AdoptedArea.DoesNotExist:
        return JsonResponse({"success": False, "message": "Adopted area not found"}, status=404)