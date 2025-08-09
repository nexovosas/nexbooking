# app/api/v1/test_email.py
from fastapi import APIRouter
from app.utils.email_utils import send_booking_confirmation_email

router = APIRouter(prefix="/test-email", tags=["test-email"])

@router.post("/")
async def test_email(to: str):
    await send_booking_confirmation_email(
        to_email=to,
        booking_details="This is a test booking confirmation from Nexovo."
    )
    return {"message": f"Email sent to {to}"}
