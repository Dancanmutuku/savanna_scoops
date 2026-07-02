# Savanna Scoops

Savanna Scoops is a Django app for an ice cream shop with customer checkout, inventory/admin views, orders, and M-Pesa payment callbacks.

This guide shows how to run it locally on your machine without Docker.

## Requirements

- Python 3.13 or newer
- Git
- ngrok, for public M-Pesa callback URLs
- A terminal such as PowerShell or Command Prompt

Check Python:

```bash
python --version
```

## 1. Create And Activate A Virtual Environment

From the project folder:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

When the environment is active, your terminal prompt usually shows `(.venv)`.

## 2. Install Dependencies

Install everything from `requirements.txt`:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Whenever `requirements.txt` changes, run this again:

```bash
python -m pip install -r requirements.txt
```

## 3. Create Your Local Environment File

Copy the example file:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

For local development, keep these values:

```env
DEBUG=True
USE_SQLITE=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

`USE_SQLITE=True` tells Django to use the local `db.sqlite3` file. This avoids depending on the remote production database while you are developing locally.

## 4. Set Up The Local Database

Run migrations:

```bash
python manage.py migrate
```

Optional: load demo shop data:

```bash
python manage.py seed_data
```

Optional: create your own admin user:

```bash
python manage.py createsuperuser
```

## 5. Run The Local Server

Start Django:

```bash
python manage.py runserver 127.0.0.1:8000
```

Open:

- Customer site: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin-panel/`
- Django admin: `http://localhost:8000/django-admin/`

Stop the server with `Ctrl+C`.

## 6. Use ngrok For M-Pesa Callbacks

M-Pesa needs a public HTTPS URL to call your local machine. In a second terminal, run:

```bash
ngrok http 8000
```

ngrok will show a forwarding URL like:

```text
https://your-ngrok-domain.ngrok-free.dev
```

Update `.env` with that domain:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,your-ngrok-domain.ngrok-free.dev
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://your-ngrok-domain.ngrok-free.dev
MPESA_CALLBACK_URL=https://your-ngrok-domain.ngrok-free.dev/payments/mpesa/callback/
```

Restart the Django server after changing `.env`.

You can inspect ngrok traffic here:

```text
http://127.0.0.1:4040
```

## 7. M-Pesa Sandbox Variables

Fill these in inside `.env` when testing M-Pesa:

```env
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=174379
MPESA_PASSKEY=
MPESA_CALLBACK_URL=https://your-ngrok-domain.ngrok-free.dev/payments/mpesa/callback/
MPESA_ENVIRONMENT=sandbox
```

Do not commit real secrets to Git.

## Deploying To Railway

Railway deployment notes live in `DEPLOYMENT.md`.

Short version:

- Add a Railway PostgreSQL service.
- Set `DATABASE_URL=${{Postgres.DATABASE_URL}}`.
- Set `USE_SQLITE=False`.
- Set `EMAIL_DELIVERY_BACKEND=resend`.
- Put your Resend API key in Railway Variables as `RESEND_API_KEY`.
- Use a verified Resend sender email as `DEFAULT_FROM_EMAIL`.

## Troubleshooting

If dependencies are missing, make sure the virtual environment is active, then run:

```bash
python -m pip install -r requirements.txt
```

If Django tries to connect to a remote Postgres database locally, check `.env`:

```env
USE_SQLITE=True
```

If port `8000` is already in use on Windows:

```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

If ngrok callbacks do not arrive, confirm:

- Django is running on `http://localhost:8000`
- ngrok is forwarding to port `8000`
- `MPESA_CALLBACK_URL` uses the current ngrok HTTPS URL
- the ngrok host is listed in `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS` includes the ngrok HTTPS origin
