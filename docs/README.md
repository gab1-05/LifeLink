# LifeLink

**LifeLink** is a web platform that connects blood donors with hospitals and patients in real time. It streamlines urgent blood requests, intelligently matches donors by blood type and proximity, and keeps all parties informed through live notifications and in-app messaging.

---

## Features

| Category | Details |
|---|---|
| **Authentication** | Email/password login, Google OAuth2, OTP-based password reset, login alerts via email |
| **Role-based Access** | Separate dashboards for **Donors**, **Hospitals**, and **Patients** |
| **Blood Requests** | Hospitals create requests with urgency levels (Critical → Low); donors receive instant alerts |
| **Smart Donor Matching** | Matches donors by compatible blood type, GPS distance, and availability |
| **Interactive Map** | Leaflet.js map showing nearby hospitals and active blood requests |
| **Real-time Messaging** | Django Channels (WebSocket) powered in-app chat between users |
| **Notifications** | In-app notification centre + email alerts for logins, matches, and requests |
| **Donor Ratings** | Hospitals and patients can rate donors after a completed donation |
| **Donation History** | Full audit trail of every donation per donor |
| **Security** | Argon2 password hashing, CSRF protection, account lockout on failed logins, masked IPs in alerts |

---

## Tech Stack

### Backend
- **Python 3** / **Django 4.2** — Web framework & ORM
- **Django Channels 4** + **Daphne** — WebSocket / ASGI server for real-time features
- **Celery 5** + **Redis** — Async task queue (SMS alerts, email jobs)
- **WhiteNoise** — Static file serving
- **MySQL** (production) / **SQLite** (development)

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript** — Server-rendered templates via Django's template engine
- **Leaflet.js** — Interactive geolocation maps
- **Google OAuth2** (`social-auth-app-django`) — One-click sign-in

### Infrastructure & Libraries
- **Gunicorn** — WSGI process manager
- **python-decouple / python-dotenv** — Environment variable management
- **PyJWT + cryptography** — JWT token utilities
- **Pillow** — Image handling
- **pymysql** — MySQL driver

---

## Getting Started

### Prerequisites

- Python 3.10+
- Redis (for Channels & Celery)
- MySQL (optional; SQLite works out of the box)

### 1. Clone the repository

```bash
git clone https://github.com/gab1-05/LifeLink.git
cd LifeLink/lifelink-frontend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example below into a `.env` file at the root of `lifelink-frontend/`:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_TIME_ZONE=Asia/Kolkata

# Leave blank to use SQLite, or set to mysql
DB_ENGINE=
DB_NAME=lifelink_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=<your-google-client-id>
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=<your-google-client-secret>

# Email (defaults to console backend in development)
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Apply migrations & seed data

```bash
python manage.py migrate
python seed_data.py   # optional: populates demo donors, hospitals & requests
```

### 6. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

> **Real-time features** (WebSocket chat & live notifications) require Daphne:
> ```bash
> daphne -b 127.0.0.1 -p 8000 lifelink.asgi:application
> ```

---

## Project Structure

```
lifelink-frontend/
├── donors/                  # Core Django app
│   ├── models.py            # UserProfile, DonorProfile, BloodRequest, etc.
│   ├── views.py             # Page views & REST API endpoints
│   ├── urls.py              # URL routing
│   ├── consumers.py         # WebSocket consumers (Django Channels)
│   ├── services.py          # SMS alert integration
│   ├── templates/           # HTML templates
│   └── static/              # App-level CSS / JS (including map.js)
├── lifelink/                # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py              # ASGI entry point (Channels)
│   └── wsgi.py
├── static/                  # Project-wide static assets
├── staticfiles/             # Collected static files (after collectstatic)
├── requirements.txt
├── manage.py
└── seed_data.py             # Demo data seeder
```

---

## Key URL Routes

| Path | Description |
|---|---|
| `/` | Landing page |
| `/login/` | Login (email or Google OAuth2) |
| `/register/` | User registration |
| `/forgot-password/` | OTP-based password reset |
| `/dashboard/` | Role-specific dashboard |
| `/map/` | Interactive donor/hospital map |
| `/requests/` | Blood request listing & management |
| `/messages/` | Real-time chat |
| `/donors/` | Browse available donors |
| `/profile/` | User profile & settings |
| `/api/...` | REST API endpoints |

---

## Environment & Deployment Notes

- **Static files**: served via WhiteNoise in production; run `collectstatic` before deploying.
- **Database**: configure `DB_ENGINE=mysql` and supply credentials via `.env` for production.
- **HTTPS**: set `DJANGO_DEBUG=False` to automatically enable HSTS, SSL redirect, and secure cookies.
- **Reverse proxy**: `SECURE_PROXY_SSL_HEADER` is pre-configured for nginx / ngrok setups.
- **Celery workers**: start a separate worker process with `celery -A lifelink worker -l info` for background tasks.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "feat: add your feature"`)
4. Push to your branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is released under the [MIT License](LICENSE).
