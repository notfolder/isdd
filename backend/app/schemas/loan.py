from pydantic import BaseModel


class LoanCreate(BaseModel):
    user_login_id: str
    loan_date: str
