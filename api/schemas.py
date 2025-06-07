from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from .models import Team
from geojson_pydantic import Point as GeoJSONPoint


# 🔹 Used for adopting an area
class AdoptAreaInput(BaseModel):
    area_name: str = Field(..., max_length=100)
    adoptee_name: str = Field(..., max_length=100)
    email: EmailStr
    adoption_type: str = Field(..., pattern="^(indefinite|temporary)$")
    end_date: Optional[date] = None
    note: str = Field('', max_length=500)
    location: GeoJSONPoint
    city: str
    state: str
    country: str

    @field_validator("end_date", mode="before")
    def blank_string_to_none(cls, v):
        return None if v in ("", None) else v



# 🔹 Used to display adopted areas on the map
class AdoptAreaLayer(BaseModel):
    id: int
    area_name: str
    adoptee_name: str
    email: EmailStr
    location: GeoJSONPoint
    city: str
    state: str
    country: str
    note: str


# 🔹 Used to create a team
class TeamCreate(BaseModel):
    name: str
    description: str
    headquarters: GeoJSONPoint
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


# 🔹 Used to return team details
class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    headquarters: GeoJSONPoint
    leader_ids: List[int]
    member_ids: List[int]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_team(cls, team: Team) -> "TeamOut":
        return cls(
            id=team.id,
            name=team.name,
            description=team.description,
            headquarters=GeoJSONPoint(
                coordinates=[team.headquarters.x, team.headquarters.y],
                type="Point"
            ) if team.headquarters else None,
            leader_ids=list(team.leaders.values_list('id', flat=True)),
            member_ids=list(team.members.values_list('id', flat=True)),
        )
