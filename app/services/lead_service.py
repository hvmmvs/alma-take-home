from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import Lead, LeadState
from app.services.email_service import EmailService
from app.services.file_service import save_resume


async def create_lead(
    db: AsyncSession,
    email_service: EmailService,
    first_name: str,
    last_name: str,
    email: str,
    resume: UploadFile | None = None,
) -> Lead:
    resume_path = None
    if resume:
        resume_path = await save_resume(resume)

    lead = Lead(
        first_name=first_name,
        last_name=last_name,
        email=email,
        resume_path=resume_path,
    )
    db.add(lead)
    await db.flush()
    await db.refresh(lead)

    # Notify the prospect
    await email_service.send_email(
        to=email,
        subject="Thank you for your submission",
        body=f"Hi {first_name}, we have received your information and will be in touch soon.",
    )
    # Notify attorney
    await email_service.send_email(
        to=settings.ATTORNEY_EMAILS[0],
        subject="New lead submitted",
        body=f"New lead: {first_name} {last_name} ({email})",
    )

    return lead


async def list_leads(db: AsyncSession) -> list[Lead]:
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    return list(result.scalars().all())


async def get_lead(db: AsyncSession, lead_id: str) -> Lead:
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )
    return lead


async def update_lead_state(
    db: AsyncSession, email_service: EmailService, lead_id: str, new_state: LeadState
) -> Lead:
    lead = await get_lead(db, lead_id)

    if lead.state != LeadState.PENDING or new_state != LeadState.REACHED_OUT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only transition from PENDING to REACHED_OUT",
        )

    lead.state = new_state
    await db.flush()
    await db.refresh(lead)

    # Notify prospect
    await email_service.send_email(
        to=lead.email,
        subject="An attorney has reached out",
        body=f"Hi {lead.first_name}, an attorney has reviewed your case and will be in contact shortly.",
    )
    # Notify attorney
    await email_service.send_email(
        to=settings.ATTORNEY_EMAILS[0],
        subject="Lead marked as reached out",
        body=f"Lead {lead.first_name} {lead.last_name} ({lead.email}) has been marked as REACHED_OUT.",
    )

    return lead
