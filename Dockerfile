FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

RUN mkdir -p media
RUN mkdir -p credentials

RUN useradd -u 10014 botuser
RUN chown -R botuser:botuser /app
USER 10014

CMD sh -c "echo \"$GOOGLE_CREDS_JSON\" > credentials/sheets-access.json && python -m src.bot"