# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

Le but de l'outil est de recommander des ressources à des primo-arrivants (migrants) selon leur profil via un modèle de recommandation de type arbre décisionnel interactif. 

les ressources sont regroupées en catégories comme l'argent, le travail, etc

à l'arrivée sur la plateforme ils doivent renseigner des infos comme s'ils ont des enfants etc

par défaut tu dois m'écrire le texte de l'app en anglais

/!\ important, l'app doit être écrite en FALC, la méthode d'écriture simplifiée!
## Responsive

l'app est pensée pour mobile, c'est la priorité, en revanche le support ordinateur doit aussi être ergonomique et fonctionnel tout de même.
## Architecture

Full-stack project with a Django REST API backend and a Vue 3 frontend. The two run as separate dev servers and communicate via HTTP — CORS is already configured.

- **Backend** (`backend/`): Django 6 + Django REST Framework + SQLite. Django project config lives in `backend/config/` (settings, urls, wsgi/asgi). The main app is `backend/pin_prototype/`.
- **Frontend** (`frontend/`): Vue 3 + Vite. Source in `frontend/src/`. The `@` alias maps to `frontend/src/`.

## Commands

### Backend
```bash
cd backend
source venv/Scripts/activate   # Windows: venv\Scripts\activate
python manage.py runserver      # http://localhost:8000
python manage.py migrate
python manage.py makemigrations
python manage.py test pin_prototype
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build
```

## Key config

- CORS allows `http://localhost:5173` (frontend dev server) — see `backend/config/settings.py`
- API routes go in `backend/config/urls.py`
- Models, views, serializers go in `backend/pin_prototype/`
- Django admin available at `/admin/`
