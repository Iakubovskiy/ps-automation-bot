# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-Marketplace Hub PIM (Product Information Management) platform. Users collect product data via a Telegram bot, enrich it with AI (Google Gemini), and publish to marketplaces (Horoshop via Playwright, Rozetka via XML feed). Multi-tenant SaaS with organizations as tenants.

## Tech Stack

- **Python 3.12**, **Django 5.0** + **Django Ninja** (REST API)
- **Aiogram 3.10** (Telegram bot with FSM)
- **Celery + Redis** (async task queue)
- **PostgreSQL** (database), **MinIO** (S3-compatible media storage)
- **Playwright** (browser automation for Horoshop publishing)
- **Google Gemini API** (AI content generation)

## Build & Run

```bash
# Docker (recommended) — starts postgres, redis, minio, django, bot, celery worker, nginx
docker-compose up --build

# Local development (requires running postgres, redis, minio)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # Django on :8000
python src/bot.py                   # Telegram bot (separate terminal)
celery -A framework.celery worker --loglevel=info  # Celery worker (separate terminal)

# Django management
python manage.py makemigrations
python manage.py migrate
```

No test suite exists yet.

## Architecture

DDD with Clean Architecture. Source code lives in `src/`.

### Module Structure (`src/modules/`)

Each module follows: `domain/` → `application/` (use cases) → `infrastructure/` (repos, services)

- **users** — User, Organization, Role entities. Multi-tenancy root.
- **catalog** — Product (DRAFT → AI_PROCESSING → READY), ProductSchema (with `attribute_schema` and `system_prompt`), ProductSchemaField (dynamic form fields), StaticReference (lookup tables).
- **distribution** — DistributionDriver (marketplace config), DistributionTask (publish status). Horoshop integration via Playwright in `drivers/horoshop/`. Rozetka integration via XML feed in `infrastructure/integrations/rozetka/`.
- **billing** — Placeholder, not implemented.
- **interface/bot_interface** — Aiogram handlers. `dynamic_collector/` is the main product creation flow using FSM states.
- **interface/web_interface** — Django Ninja API actions under `actions/`.

### Event-Driven Async Flow

`core/events/event_bus.py` dispatches domain events as Celery tasks:

1. Bot collects product data → `CreateProductUseCase` → publishes `ProductCreatedEvent`
2. `ProductCreatedEvent` → Celery task → `GenerateAiContentUseCase` (calls Gemini API) → publishes `ProductEnrichedEvent`
3. `ProductEnrichedEvent` → Celery task → `PublishProductUseCase` (Playwright automation to Horoshop; passive drivers like Rozetka are skipped)

Celery task discovery is configured in `src/framework/celery.py` via `CELERY_IMPORTS`.

### Marketplace Integrations

| Platform | Model | How it works |
|---|---|---|
| Horoshop | Push (Playwright) | ProductEnrichedEvent → Celery → browser automation via HoroshopManifest steps |
| Rozetka | Pull (XML feed) | Rozetka crawls `GET /feed/rozetka/<feed_token>/`. All READY products with mapped schemas appear automatically |

### Key Entry Points

- `src/bot.py` — Bot startup (asyncio main loop)
- `src/framework/settings.py` — Django config, env vars
- `src/framework/urls.py` — API routing (`/api/`) + Rozetka feed (`/feed/rozetka/<token>/`)
- `src/modules/interface/bot_interface/handlers/dynamic_collector/entrypoint.py` — `/start` command

### Data Model Notes

- UUID primary keys everywhere
- `Product.attributes` and `ProductSchema.attribute_schema` are JSONFields
- `ProductSchemaField` model defines dynamic form fields (source_type: STATIC_DB, MANUAL, BOOLEAN)
- ForeignKeys use PROTECT delete policy
- Org ID is denormalized across Product, DistributionDriver, DistributionTask
- Rozetka config: `RozetkaFeedConfig` (per driver), `RozetkaCategoryMapping` (schema → Rozetka category), `RozetkaFieldMapping` (attribute → XML field)

## Exposed Ports (Docker)

- Django: 8000, Nginx: 80, MinIO console: 9001, Postgres: 5433, Redis: 6379, Telegram API: 8081
