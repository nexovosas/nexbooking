FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Instala deps de Python
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el código (no copies .env)
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# Usuario no-root
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# (si NO quieres correr migraciones aquí, elimina el ENTRYPOINT)
# ENTRYPOINT ["sh", "-c", "alembic upgrade head && exec \"$@\""]
# CMD por defecto: Gunicorn + Uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", "--threads", "4", "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-"]
