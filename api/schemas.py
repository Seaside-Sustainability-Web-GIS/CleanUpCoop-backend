from pydantic import BaseModel
from ninja import Schema

class SignInSchema(BaseModel):
    email: str
    password: str

class ForgotPasswordSchema(Schema):
    email: str

class ResetPasswordSchema(Schema):
    uid: str
    token: str
    new_password: str
