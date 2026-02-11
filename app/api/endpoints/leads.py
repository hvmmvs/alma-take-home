from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.schemas.lead import LeadCreateResponse, LeadDetailResponse, LeadUpdateStateRequest
from app.services.email_service import EmailService, get_email_service
from app.services.lead_service import create_lead, get_lead, list_leads, update_lead_state

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LeadCreateResponse)
async def submit_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: EmailStr = Form(...),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
) -> LeadCreateResponse:
    lead = await create_lead(
        db=db,
        email_service=email_service,
        first_name=first_name,
        last_name=last_name,
        email=email,
        resume=resume,
    )
    return LeadCreateResponse.model_validate(lead)


@router.get("", response_model=list[LeadDetailResponse])
async def get_leads(
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LeadDetailResponse]:
    leads = await list_leads(db)
    return [LeadDetailResponse.model_validate(lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead_by_id(
    lead_id: str,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeadDetailResponse:
    lead = await get_lead(db, lead_id)
    return LeadDetailResponse.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadDetailResponse)
async def patch_lead(
    lead_id: str,
    body: LeadUpdateStateRequest,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeadDetailResponse:
    lead = await update_lead_state(db, lead_id, body.state)
    return LeadDetailResponse.model_validate(lead)
