# FinOps — AWS Cloud Cost Optimization Platform

A modular FastAPI backend for multi-tenant AWS cost visibility, resource inventory, and savings recommendations.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env       # then edit .env with your values

# 4. Create database tables
python -m migrations.create_tables

# 5. Run the API server
uvicorn app.main:app --reload --port 8000

# 6. (Optional) Start Celery worker
celery -A app.core.celery_app worker --loglevel=info
```

## API Docs

Once running, visit **http://localhost:8000/docs** for the interactive Swagger UI.

## Project Structure

```
app/
├── api/v1/          # Versioned REST endpoints
├── core/            # Config, Celery setup
├── db/              # Engine, session, base
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request / response schemas
├── services/        # AWS STS, Cost Explorer, CloudWatch
└── tasks/           # Celery async tasks
```
