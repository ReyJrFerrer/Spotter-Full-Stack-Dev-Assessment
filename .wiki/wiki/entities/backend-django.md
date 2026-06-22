---
title: "Django Backend Structure"
type: entity
summary: "Current structure and planned implementation for the Django backend (spotter-bed/)"
tags: [backend, django, drf, python]
date: 2026-06-22
confidence: medium
sources:
  - raw/articles/backend-specifications.md
  - raw/notes/project-codebase-state.md
  - raw/notes/tech-stack-details.md
---

# Django Backend Structure

## Current State

The `spotter-bed/` directory contains a scaffolded Django 6.0.6 project:

```
spotter-bed/
├── Pipfile              # Only django listed
├── venv/                # Python 3.14 virtual environment
└── backend/
    ├── manage.py
    ├── db.sqlite3
    ├── backend/         # Django project config
    │   ├── settings.py  # Default config (no DRF, no corsheaders)
    │   ├── urls.py      # Only /admin/ route
    │   └── ...
    └── spotter-eld/     # Django app (empty scaffold)
        ├── models.py    # No models
        ├── views.py     # No views
        ├── admin.py
        ├── apps.py
        └── tests.py
```

## What Needs Building

Per the [[api-specification|API Specification]]:

1. **Install dependencies**: `djangorestframework`, `django-cors-headers`
2. **Register apps**: Add `spotter_eld`, `rest_framework`, `corsheaders` to `INSTALLED_APPS`
3. **CORS config**: Whitelist frontend origin
4. **DRF endpoint**: `POST /api/trips/generate/`
   - Serializer: validate `current_location`, `pickup_location`, `dropoff_location`, `current_cycle_used_hrs`
   - View: call HOS engine, return route + stops + daily logs
5. **Port HOS engine**: Translate `hosSimulator.ts` (TypeScript) to Python
6. **Map API**: Integrate free Map API for distance/path calculation

## Spotter-ELD App

The `spotter_eld` app is intended to house:
- HOS algorithm engine (Python)
- Route calculation logic
- ELD log data generation
- DRF views and serializers

## Cross-References

- [[hours-of-service|FMCSA HOS Rules]] — the business logic to implement
- [[project-architecture|Project Architecture]] — overall system design
- [[api-specification|API Specification]] — endpoint details
