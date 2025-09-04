import functools
import json

from django.db import transaction
from geojson_pydantic import Point
from django.contrib.gis.geos import GEOSGeometry
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from ninja.errors import HttpError

from .models import AdoptedArea, Team
from .schemas import AdoptAreaInput, AdoptAreaLayer, TeamCreate, TeamOut, LeaderRequest
from typing import List

User = get_user_model()

api = NinjaAPI(
    csrf=False,
    title="Seaside Sustainability WebGIS API",
    description="API for managing adopted areas and teams in the Seaside Sustainability WebGIS application.",
)


def require_auth(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        session_token = request.headers.get("X-Session-Token")
        user = get_user_from_token(session_token)
        if not user:
            return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)
        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapper


def require_team_leader(user, team):
    if user not in team.leaders.all():
        return JsonResponse({"success": False, "message": "You are not a team leader"}, status=403)


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
@require_auth
def adopt_area(request, data: AdoptAreaInput):
    try:
        if data.adoption_type == "temporary" and not data.end_date:
            return JsonResponse(
                {"success": False, "message": "end_date is required for temporary adoption."},
                status=400,
            )

        lng, lat = data.location.coordinates
        point = GEOSGeometry(f'POINT({lng} {lat})', srid=4326)

        payload = {
            "user": request.user,
            "area_name": data.area_name.strip(),
            "adoptee_name": data.adoptee_name.strip(),
            "email": str(data.email),
            "adoption_type": data.adoption_type,
            "end_date": data.end_date,
            "is_active": data.is_active,
            "note": data.note.strip(),
            "location": point,
            "city": data.city.strip(),
            "state": data.state.strip(),
            "country": data.country.strip(),
        }

        with transaction.atomic():
            obj = AdoptedArea.objects.create(**payload)

        return JsonResponse(
            {"success": True, "message": "Area adopted successfully!", "id": obj.id},
            status=201,
        )

    except ValueError as ve:
        return JsonResponse({"success": False, "message": f"Invalid data: {ve}"}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse(
            {"success": False, "message": f"Failed to save area: {str(e)}"},
            status=500,
        )


@api.get("/adopted-area-layer/", response=List[AdoptAreaLayer], tags=["Adopt Area"])
def list_adopted_areas(request):
    try:
        return [
            AdoptAreaLayer(
                id=area.id,
                area_name=area.area_name,
                adoptee_name=area.adoptee_name,
                email=area.email,
                location={
                    "type": "Point",
                    "coordinates": [area.location.x, area.location.y]
                },
                city=area.city,
                state=area.state,
                country=area.country,
                note=area.note
            )
            for area in AdoptedArea.objects.filter(is_active=True)
        ]
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error fetching adopted areas: {str(e)}"},
            status=500
        )


@api.put("/adopt-area/{area_id}/", tags=["Adopt Area"])
@require_auth
def update_adopted_area(request, area_id: int, data: AdoptAreaInput):
    try:
        area = AdoptedArea.objects.get(id=area_id, user=request.user)
    except AdoptedArea.DoesNotExist:
        return JsonResponse({"success": False, "message": "Adopted area not found"}, status=404)

    if data.adoption_type == "temporary" and not data.end_date:
        return JsonResponse(
            {"success": False, "message": "end_date is required for temporary adoption."},
            status=400,
        )

    lng, lat = data.location.coordinates
    location_point = GEOSGeometry(f'POINT({lng} {lat})', srid=4326)

    area.area_name = data.area_name.strip()
    area.adoptee_name = data.adoptee_name.strip()
    area.email = str(data.email)
    area.adoption_type = data.adoption_type
    area.end_date = data.end_date
    area.is_active = data.is_active
    area.note = data.note.strip()
    area.location = location_point
    area.city = data.city.strip()
    area.state = data.state.strip()
    area.country = data.country.strip()
    area.save()

    return JsonResponse({"success": True, "message": "Adopted area updated successfully!"})


@api.delete("/adopt-area/{area_id}/", tags=["Adopt Area"])
@require_auth
def delete_adopted_area(request, area_id: int):
    try:
        area = AdoptedArea.objects.get(id=area_id, user=request.user)
        area.delete()
        return JsonResponse({"success": True, "message": "Adopted area deleted successfully!"})
    except AdoptedArea.DoesNotExist:
        return JsonResponse({"success": False, "message": "Adopted area not found"}, status=404)

    # -------------------- TEAMS --------------------


@api.get("/teams/", response=List[TeamOut], tags=["Teams"])
def list_teams(request):
    return [
        TeamOut(
            id=team.id,
            name=team.name,
            description=team.description,
            headquarters=Point(**json.loads(team.headquarters.geojson)),
            city=team.city,
            state=team.state,
            country=team.country,
            member_ids=list(team.members.values_list("id", flat=True)),
            leader_ids=list(team.leaders.values_list("id", flat=True)),
        )
        for team in Team.objects.all()
    ]


@api.get("/teams/{team_id}/", response=TeamOut, tags=["Teams"])
def get_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return TeamOut(
        id=team.id,
        name=team.name,
        description=team.description,
        headquarters=Point(**json.loads(team.headquarters.geojson)),
        city=team.city,
        state=team.state,
        country=team.country,
    )


@api.put("/teams/{team_id}/", response=TeamOut, tags=["Teams"])
@require_auth
def update_team(request, team_id: int, payload: TeamCreate):
    team = get_object_or_404(Team, id=team_id)

    permission_check = require_team_leader(request.user, team)
    if permission_check:
        return permission_check  # Returns JsonResponse with 403

    team.name = payload.name
    team.description = payload.description
    team.headquarters = payload.headquarters
    team.save()
    return team


@api.delete("/teams/{team_id}/", tags=["Teams"])
@require_auth
def delete_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)

    permission_check = require_team_leader(request.user, team)
    if permission_check:
        return permission_check

    team.delete()
    return JsonResponse({"success": True, "message": "Team deleted successfully"})


@api.post("/teams/", response=TeamOut, tags=["Teams"])
@require_auth
def create_team(request, payload: TeamCreate):
    geojson = payload.headquarters
    django_point = GEOSGeometry(json.dumps(geojson))

    team = Team.objects.create(
        name=payload.name,
        description=payload.description,
        headquarters=django_point,
        city=payload.city,
        state=payload.state,
        country=payload.country
    )
    team.members.add(request.user)
    team.leaders.add(request.user)
    return TeamOut(
        id=team.id,
        name=team.name,
        description=team.description,
        headquarters=json.loads(team.headquarters.geojson),
        city=team.city,
        state=team.state,
        country=team.country,
        member_ids=list(team.members.values_list("id", flat=True)),
        leader_ids=list(team.leaders.values_list("id", flat=True)),
    )


@api.post("/teams/{team_id}/join", tags=["Teams"])
@require_auth
def join_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    team.members.add(request.user)
    return {"success": True}


@api.post("/teams/{team_id}/leave", tags=["Teams"])
@require_auth
def leave_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    team.members.remove(request.user)
    team.leaders.remove(request.user)
    return {"success": True}


def is_team_leader(user, team: Team):
    return user in team.leaders.all()


@api.post("/teams/{team_id}/add_leader/", tags=["Teams"])
@require_auth
def add_leader(request, team_id: int, payload: LeaderRequest):
    team = get_object_or_404(Team, id=team_id)

    if not is_team_leader(request.user, team):
        raise HttpError(403, "Only team leaders can add other leaders.")

    if team.leaders.count() >= 5:
        raise HttpError(400, "Maximum number of team leaders reached.")

    user = get_object_or_404(User, id=payload.user_id)

    if user not in team.members.all():
        raise HttpError(400, "User must be a team member before becoming a leader.")

    team.leaders.add(user)
    return {"success": True, "message": f"{user.username} is now a team leader."}


@api.post("/teams/{team_id}/remove_leader/", tags=["Teams"])
def remove_leader(request, team_id: int, payload: LeaderRequest):
    team = get_object_or_404(Team, id=team_id)

    if not is_team_leader(request.user, team):
        raise HttpError(403, "Only team leaders can remove leaders.")

    user = get_object_or_404(User, id=payload.user_id)

    if user not in team.leaders.all():
        raise HttpError(400, "User is not a leader.")

    if team.leaders.count() == 1:
        raise HttpError(400, "Cannot remove the last remaining team leader.")

    team.leaders.remove(user)
    return {"success": True, "message": f"{user.username} is no longer a team leader."}
