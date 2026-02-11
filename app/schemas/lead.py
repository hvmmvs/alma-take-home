from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.lead import LeadState


class LeadCreateResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    resume_path: str
    state: LeadState
    created_at: datetime


class LeadDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    resume_path: str
    state: LeadState
    created_at: datetime
    updated_at: datetime


class LeadUpdateStateRequest(BaseModel):
    state: LeadState
