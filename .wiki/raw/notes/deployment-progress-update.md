---
title: "Deployment Progress Update"
type: note
summary: "Track record of Vercel deployment configuration commits spanning settings churn, WSGI module resolution, CORS, and env-driven config."
tags: [deployment, vercel, backend, frontend, infrastructure]
date: 2026-06-24
confidence: high
source: git log - git diff analysis of commits 780568d..0660301
---

# Deployment Progress Update

## Overview

On June 24, 2026, the Spotter Assessment project underwent a deployment configuration session consisting of 7 commits over ~2 hours. The goal was to configure both the Django backend and React frontend for Vercel deployment. The session involved significant back-and-forth on settings.py structure, WSGI module resolution, and CORS configuration.

## Commit Chain

### 1. `780568d` — "feat: Deployment configurations for backend and frontend" (16:45)

**Files changed:** 12 files, +52/-114

Initial deployment configuration commit. Added:
- `spotter-bed/.python-version` — Python 3.12
- `spotter-bed/.vercelignore` — excludes venv/, __pycache__, tests/
- `spotter-bed/requirements.txt` — Django 6.0.6, DRF 3.17.1, django-cors-headers 4.9.0
- `spotter-bed/pyproject.toml` — Vercel entrypoint `backend.backend.wsgi:application`
- `spotter-bed/vercel.json` — WSGI build config
- `spotter-fed/vercel.json` — SPA rewrites to index.html

Heavily modified `settings.py`: stripped `django.contrib.contenttypes` and `django.contrib.auth` from INSTALLED_APPS for minimal Vercel footprint. Removed `backend/urls.py` root URL config. Made `settings.py` env-driven for secret key, debug, CORS.

**Decision:** Adopt env-driven configuration model for Vercel compatibility. Strip unnecessary Django contrib apps for minimal deployment.

### 2. `f876638` — "Configure for Vercel deployment: stateless Django, Python 3.12, SPA routing" (16:46)

**Files changed:** 1 file, -15

Deleted `spotter-bed/vercel.json` entirely. Likely a mistaken revert — the config was restored in the next commit.

### 3. `13b282d` — "Re: Reapply settings" (16:57)

**Files changed:** 3 files, +25/-13

Restored `vercel.json` with identical content. Deleted `pyproject.toml` — consolidated Vercel config into `vercel.json` only. Made `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` env-driven via comma-separated env vars. Added conditional `DATABASES` — empty dict when `VERCEL` env is set, SQLite otherwise. Kept `contenttypes` and `auth` removed.

**Decision:** Remove pyproject.toml in favor of vercel.json-only config. Make DB stateless on Vercel via `VERCEL` env flag.

### 4. `91ddaa7` — "Updates on the wsgi to set the backend settings module" (17:04)

**Files changed:** 2 files, +7/-1

Restored `django.contrib.contenttypes` and `django.contrib.auth` in INSTALLED_APPS — likely needed by DRF or middleware. Added `sys.path.insert(0, _base)` in `wsgi.py` to ensure the `backend` Python package is resolvable when Vercel runs the WSGI app.

**Decision:** Contenttypes and auth are required after all — restored. WSGI needs path manipulation for Vercel's execution environment.

### 5. `c12fea0` — "Re: Settings update" (18:19)

**Files changed:** 2 files, +14/-1

Fixed `WSGI_APPLICATION` from `backend.wsgi.app` to `backend.wsgi.application` (correct WSGI callable name). Added CORS empty-string filter `[o for o in CORS_ALLOWED_ORIGINS if o]` to handle trailing comma edge cases. Added API root endpoint at `""` returning service metadata JSON. Added trailing slash stripping on `VITE_API_URL` — changed to `(import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')`.

**Decision:** Fix WSGI callable name mismatch. Defensive CORS list filtering. Add API root discovery endpoint.

### 6. `92d59ab` — "Strip any trailing slash" (18:39)

**Files changed:** 1 file, +1/-1

Applied trailing slash strip to `VITE_API_URL` in `App.tsx`. This commit applied the code change that was described in c12fea0's message but may have been missed.

### 7. `0660301` — "Allowing CORS Origin for localhost:5173" (19:05)

**Files changed:** 3 files, +5/-3

Changed default `CORS_ALLOWED_ORIGINS` from `localhost:3000` to `localhost:5173` (Vite default port). Added `.env` to both backend and frontend `.gitignore` files.

**Decision:** Frontend dev server migrated from port 3000 to 5173. Env files should not be committed.

## Key Decision Points

1. **Build tool**: `@vercel/python` with WSGI entrypoint for backend; SPA rewrites for frontend
2. **Python version**: 3.12 (specified in `.python-version`)
3. **Stateless DB**: `DATABASES = {}` when `VERCEL` env is present, SQLite for local dev
4. **Env-driven config**: `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `SECRET_KEY`, `DEBUG` all via env vars
5. **Module resolution**: `sys.path.insert(0, _base)` hack in `wsgi.py` needed for Vercel
6. **CORS port change**: `3000` → `5173` (Vite default)
7. **No pyproject.toml**: All Vercel config consolidated in `vercel.json`
8. **Installed apps**: `contenttypes` + `auth` initially removed, then restored

## Current Configuration State

### Backend (`spotter-bed/`)

| Artifact | Purpose | Content |
|---|---|---|
| `vercel.json` | Build/routes config | WSGI builds from `backend/backend/wsgi.py` |
| `.vercelignore` | Exclusion rules | Skips venv/, __pycache__, tests/ |
| `requirements.txt` | Dependencies | Django 6.0.6, DRF 3.17.1, cors-headers 4.9.0 |
| `.python-version` | Python version | 3.12 |
| `settings.py` | Env-driven config | Conditional DB, env-driven ALLOWED_HOSTS/CORS |
| `wsgi.py` | WSGI entrypoint | sys.path hack for module resolution |
| `urls.py` (spotter_eld) | API routes | Root endpoint, /api/health/, /api/trips/generate/ |

### Frontend (`spotter-fed/`)

| Artifact | Purpose | Content |
|---|---|---|
| `vercel.json` | SPA rewrites | All routes → `/index.html` |
| `App.tsx` | API URL handling | Trailing slash strip on `VITE_API_URL` |

## Files Touched

```
spotter-bed/.gitignore
spotter-bed/.python-version
spotter-bed/.vercelignore
spotter-bed/Pipfile
spotter-bed/backend/backend/settings.py
spotter-bed/backend/backend/wsgi.py
spotter-bed/backend/backend/urls.py
spotter-bed/backend/spotter_eld/urls.py
spotter-bed/pyproject.toml (added then deleted)
spotter-bed/requirements.txt
spotter-bed/vercel.json (added → deleted → re-added)
spotter-fed/.gitignore
spotter-fed/src/App.tsx
spotter-fed/src/vite-env.d.ts
spotter-fed/vercel.json
```

## Cross-References

- [[project-architecture|Project Architecture Reference]] — architecture overview
- [[backend-django|Django Backend Structure]] — backend implementation details
