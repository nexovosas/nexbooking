import os
import ssl
import asyncio
import aiosmtplib
from email.message import EmailMessage
from email.utils import make_msgid, formatdate



def _build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # Opcional endurecimiento:
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx

async def send_booking_confirmation_email(
    to_email: str,
    booking_details: str,
    subject: str = "Booking Confirmation",
    html_body: str | None = None,
    reply_to: str | None = None,
    max_retries: int = 3,
):
    # Construcción del mensaje
    message = EmailMessage()
    sender = os.getenv("SMTP_FROM", os.getenv("EMAIL_HOST_USER", "noreply@nexovo.com.co"))
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    message["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    message["Date"] = formatdate(localtime=True)
    if reply_to := (reply_to or os.getenv("SMTP_REPLY_TO", "")):
        message["Reply-To"] = reply_to

    # Parte de texto plano (siempre)
    text_body = f"Your booking was successful:\n\n{booking_details}"
    message.set_content(text_body)

    # Alternativa HTML (opcional, recomendable para clientes modernos)
    if html_body is None:
        html_body = f"""
        <html>
          <body>
            <p><strong>Your booking was successful</strong></p>
            <p>{booking_details.replace('\n', '<br>')}</p>
          </body>
        </html>
        """
    message.add_alternative(html_body, subtype="html")

    # Config SMTP
    host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.getenv("EMAIL_PORT", "465"))
    user = os.getenv("EMAIL_HOST_USER")
    password = os.getenv("EMAIL_HOST_PASSWORD")
    use_ssl = os.getenv("EMAIL_USE_SSL", "true").strip().lower() == "true"

    # Timeouts razonables
    timeout = 15  # segundos

    # Envío con reintentos y backoff exponencial (1s, 2s, 4s…)
    attempt = 0
    last_err: Exception | None = None
    while attempt < max_retries:
        try:
            if use_ssl:
                # SMTPS (465) con SSL desde el inicio — recomendado para Hostinger
                await aiosmtplib.send(
                    message,
                    hostname=host,
                    port=port,
                    username=user,
                    password=password,
                    use_tls=True,
                    tls_context=_build_ssl_context(),
                    timeout=timeout,
                )
            else:
                # STARTTLS (587) si no hay SSL estricto
                await aiosmtplib.send(
                    message,
                    hostname=host,
                    port=port,
                    username=user,
                    password=password,
                    start_tls=True,
                    timeout=timeout,
                )
            return  # éxito
        except (aiosmtplib.errors.SMTPException, OSError, TimeoutError) as e:
            last_err = e
            attempt += 1
            if attempt >= max_retries:
                raise
            await asyncio.sleep(2 ** (attempt - 1))

