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
        session = Session.objects.get(session_key=token)
        user_id = session.get_decoded().get('_auth_user_id')
        return User.objects.get(id=user_id)
    except Exception:
        return None


# -------------------- CSRF --------------------
@api.get("/csrf/", tags=["Auth"])
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"success": True, "message": "CSRF cookie set"})


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
        for area in AdoptedArea.objects.all()
    ]
