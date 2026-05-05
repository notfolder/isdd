from typing import Optional
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    equipment_id: str
    name: str


class EquipmentUpdate(BaseModel):
    name: str


class LoanInfo(BaseModel):
    user_login_id: str
    user_display_name: str
    loan_date: str


class EquipmentResponse(BaseModel):
    equipment_id: str
    name: str
    status: str
    loan_info: Optional[LoanInfo] = None

    class Config:
        from_attributes = True
