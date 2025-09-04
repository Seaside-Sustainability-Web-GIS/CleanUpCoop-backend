from datetime import date
from typing import Optional, List, Literal, Tuple
from ninja import Schema
from pydantic import BaseModel, EmailStr, Field, field_validator
from geojson_pydantic import Point


class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: Tuple[float, float]

    @field_validator("coordinates")
    @classmethod
    def validate_coords(cls, v):
        if len(v) != 2:
            raise ValueError("Coordinates must be [lng, lat].")
        lng, lat = v
        if not (-180 <= lng <= 180 and -90 <= lat <= 90):
            raise ValueError("Coordinates out of range.")
        return v


class AdoptAreaInput(BaseModel):
    area_name: str = Field(..., max_length=100)
    adoptee_name: str = Field(..., max_length=100)
    email: EmailStr
    adoption_type: Literal["indefinite", "temporary"] = "indefinite"
    end_date: Optional[date] = None
    is_active: bool = True
    note: str = Field("", max_length=500)
    location: GeoJSONPoint
    city: str
    state: str
    country: str

    @field_validator("end_date", mode="before")
    @classmethod
    def blank_string_to_none(cls, v):
        return None if v in ("", None) else v


# 🔹 Used to display adopted areas on the map
class AdoptAreaLayer(BaseModel):
    id: int
    area_name: str
    adoptee_name: str
    email: EmailStr
    location: Point
    city: str
    state: str
    country: str
    note: str


# 🔹 Used to create a team
class TeamCreate(Schema):
    name: str
    description: str
    headquarters: dict  # GeoJSON Point
    city: str = ""
    state: str = ""
    country: str = ""


class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    headquarters: Point
    city: str
    state: str
    country: str
    member_ids: List[int]
    leader_ids: List[int]


# 🔹 Used to request a user to become a team leader
class LeaderRequest(Schema):
    user_id: int
