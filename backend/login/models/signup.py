from sqlmodel import SQLModel, Field
from pydantic import BaseModel, EmailStr

# Define the User model with SQLModel
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    First_Name: str
    Last_Name:str
    email: EmailStr
    password: str

# Pydantic model for registration
class UserRegistration(BaseModel):
    First_Name: str
    Last_Name:str
    email: EmailStr
    password: str
    confirm_password: str