from ninja import Schema
from pydantic import EmailStr

class RegisterSchema(Schema):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class LoginSchema(Schema):
    email: EmailStr
    password: str

class ForgotPasswordSchema(Schema):
    email: EmailStr

class ResetPasswordSchema(Schema):
    uid: str
    token: str
    new_password: str