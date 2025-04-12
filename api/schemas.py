from pydantic import BaseModel, EmailStr, Field


class AdoptAreaInput(BaseModel):
    area_name: str = Field(..., max_length=100)
    adoptee_name: str = Field(..., max_length=100)
    email: EmailStr
    note: str = Field('', max_length=500)
    lat: float
    lng: float
    city: str
    state: str
    country: str


class AdoptAreaLayer(BaseModel):
    id: int
    area_name: str
    adoptee_name: str
    email: EmailStr
    lat: float
    lng: float
    city: str
    state: str
    country: str
    note: str
