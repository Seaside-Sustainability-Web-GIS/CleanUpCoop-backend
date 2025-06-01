from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
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

    @field_validator("location")
    def validate_location_coordinates(cls, v: Point):
        coords = v.coordinates
        if not isinstance(coords, (list, tuple)) or len(coords) != 2:
            raise ValueError("Coordinates must be a [lng, lat] pair")
        lng, lat = coords
        if lng is None or lat is None:
            raise ValueError("Coordinates cannot be null")
        if not all(isinstance(c, (float, int)) for c in coords):
            raise ValueError("Coordinates must be numbers")
        return v


# 🔹 Used to display adopted areas on the map
class AdoptAreaLayer(BaseModel):
    id: int
    area_name: str
    adoptee_name: str
    email: EmailStr
    location: Dict[str, Any]
    city: str
    state: str
    country: str
    note: str


# 🔹 Used to create a team
class TeamCreate(BaseModel):
    name: str
    description: str
    headquarters: Point


# 🔹 Used to return team details
class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    headquarters: Point
    leader_ids: List[int]
    member_ids: List[int]
