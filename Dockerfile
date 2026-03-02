FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright dependencies for the worker container
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

RUN mkdir -p media
RUN mkdir -p credentials
RUN mkdir -p staticfiles

# Default command — overridden per service in docker-compose.yml
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]