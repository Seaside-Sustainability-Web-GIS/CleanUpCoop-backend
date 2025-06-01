import json
from datetime import date
from typing import Optional, List, Dict, Any

from ninja import Schema
from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer
from geojson_pydantic import Point


# 🔹 Used for adopting an area
class AdoptAreaInput(BaseModel):
    area_name: str = Field(..., max_length=100)
    adoptee_name: str = Field(..., max_length=100)
    email: EmailStr
    adoption_type: str = Field(..., pattern="^(indefinite|temporary)$")
    end_date: Optional[date] = None
    note: str = Field('', max_length=500)
    location: Point
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


# 🔹 Used to request a user to become a team leader
class LeaderRequest(Schema):
    user_id: int
