from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    login_id: str
    display_name: str
    password: str
    role: str


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    login_id: str
    display_name: str
    role: str

    class Config:
        from_attributes = True


class UserForLoan(BaseModel):
    login_id: str
    display_name: str

    class Config:
        from_attributes = True
