import os
import aiosmtplib
from email.message import EmailMessage

async def send_booking_confirmation_email(to_email: str, booking_details: str):
    message = EmailMessage()
    message["From"] = os.getenv("SMTP_FROM", "noreply@tusitio.com")
    message["To"] = to_email
    message["Subject"] = "Booking Confirmation"
    message.set_content(f"Your booking was successful:\n\n{booking_details}")

    await aiosmtplib.send(
        message,
        hostname=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        port=int(os.getenv("SMTP_PORT", 587)),
        username=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
        start_tls=True
    )
