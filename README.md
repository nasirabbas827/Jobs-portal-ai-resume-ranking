# Jobs Portal Ai Resume Ranking

Jobs-portal-ai-resume-ranking is a job portal with resume ranking and application management.

![Django](https://img.shields.io/badge/Django-2563EB?style=flat-square) ![SQLite](https://img.shields.io/badge/SQLite-0F172A?style=flat-square)

## Overview

The data model covers `JobSeeker`, `Recruiter`, `Resume`, `Company`, `Job`, `Application`, `ParsedResume`, `Communication`.

## Implemented workflows

The source defines these handlers:

- **Register Seeker** — `register_seeker`
- **Register Recruiter** — `register_recruiter`
- **Login** — `login_view`
- **Logout** — `logout_view`
- **Seeker Home** — `seeker_home`
- **Job Detail** — `job_detail`
- **Apply Job** — `apply_job`
- **My Applications** — `my_applications`
- **Recruiter Home** — `recruiter_home`
- **Index** — `index`
- **Seeker Resume** — `seeker_resume`
- **Recruiter Company** — `recruiter_company`

## Getting started

### 1. Get the project

```bash
git clone https://github.com/nasirabbas827/Jobs-portal-ai-resume-ranking.git
cd Jobs-portal-ai-resume-ranking
```

### 2. Prepare Python

Create an isolated environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows Command Prompt, or `source .venv/bin/activate` on macOS/Linux.

No requirements file is included. The inspected Python imports indicate these dependencies as a starting point:

```bash
python -m pip install Django sentence-transformers numpy textblob PyMuPDF docx2txt scikit-learn
```

Dependency versions are not pinned in this repository.

### 3. Configure and run

Review [`myproject/settings.py`](myproject/settings.py) for database, media, and any email configuration. Use a local copy of the supplied database when available.

```bash
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. If you need a Django administration account, run `python manage.py createsuperuser`. Application-specific user roles may be managed separately.

Review the application's email/API configuration and supply your own service credentials for integrations you intend to use.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`db.sqlite3`](db.sqlite3) | Included SQLite database |
| [`manage.py`](manage.py) | Django command-line entry point |
| [`myapp`](myapp) | Django application modules |
| [`myproject`](myproject) | Django project configuration |
| [`templates`](templates) | HTML page templates |

## Development notes

These setup instructions are based on the repository source. The application has not been executed as part of this documentation update; verify dependencies and configuration in your local environment.
