from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(alias="_id")
    email: EmailStr
    hashed_password: str

class UserInDB(User):
    hashed_password: str