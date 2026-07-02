# Savanna Scoops Deployment

## Docker

This project now includes a Docker stack for local and server-style runs:

- `Dockerfile` builds the Django/Gunicorn web image.
- `docker-compose.yml` runs the web app with Postgres.
- `docker-entrypoint.sh` waits for Postgres, runs migrations, collects static files, and can load starter data.
- `.env.docker` documents Docker-specific environment values you can pass with `--env-file`.

### Run locally

```bash
docker compose up --build
# or, to use values from .env.docker:
docker compose --env-file .env.docker up --build
```

Open:

- Customer site: `http://localhost:8000/`
- Admin panel: `http://localhost:8000/admin-panel/`
- Django admin: `http://localhost:8000/django-admin/`

By default, the stack uses Postgres and loads `data/render_seed.json` into an empty database. To use the richer demo data command instead, set:

```bash
SEED_DATA=1
```

The Docker database connection is pinned to the Compose `db` service so your normal app `.env` cannot accidentally send the container to an external database.

Docker runs with `DOCKER_DEBUG=True` by default for local HTTP access at `http://localhost:8000`. Set `DOCKER_DEBUG=False` only when running behind HTTPS.

### Useful Docker commands

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_data
docker compose down
docker compose down -v
```

Use `docker compose down -v` only when you want to delete the local Postgres, media, and static volumes.

## GitHub

1. Push the project to a GitHub repository.
2. Keep `.env` out of the repository.
3. Use `.env.example` as the reference for required environment variables.

## Railway

This project is ready for Railway with:

- `railway.json` for the Railway start command and healthcheck.
- `requirements.txt` for Python dependencies.
- `gunicorn` for production serving.
- WhiteNoise for static files.
- `DATABASE_URL` support for Railway Postgres.
- Resend API support for production order emails.

### Railway Setup

1. Push this repository to GitHub.
2. In Railway, create a new project.
3. Choose **Deploy from GitHub repo** and select this repo.
4. Add a PostgreSQL database service:
   - Open the project canvas.
   - Add **Database > PostgreSQL**.
5. On the Django app service, open **Variables**.
6. Paste values based on `.env.railway.example`.

For the database variable, use Railway's service reference:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_SSLMODE=require
USE_SQLITE=False
```

If your Railway Postgres service has a different name, replace `Postgres` with that service name.

### Railway Public URL

After the app deploys:

1. Open the Django app service.
2. Go to **Settings > Networking**.
3. Click **Generate Domain**.
4. Railway will provide a domain like:

```text
your-app.up.railway.app
```

Railway provides this domain at runtime as `RAILWAY_PUBLIC_DOMAIN`. The app automatically adds it to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

Set:

```env
APP_BASE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
MPESA_CALLBACK_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}/payments/mpesa/callback/
```

### Resend Email

Use Resend for production email:

```env
EMAIL_DELIVERY_BACKEND=resend
EMAIL_SEND_ASYNC=True
RESEND_API_KEY=your-resend-api-key
RESEND_API_URL=https://api.resend.com/emails
DEFAULT_FROM_NAME=Savanna Scoops
DEFAULT_FROM_EMAIL=orders@your-verified-domain.com
```

Resend requires a verified sending domain for production sending. Use an email address from that verified domain for `DEFAULT_FROM_EMAIL`.

### Railway Start Command

Railway uses `railway.json`:

```bash
python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py bootstrap_render_data && gunicorn savanna_scoops.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 60 --access-logfile - --error-logfile -
```

This command:

- runs database migrations,
- collects static files,
- loads starter data only when the database is empty,
- starts Gunicorn on Railway's assigned `$PORT`.

### Required Railway Variables

Minimum production variables:

```env
SECRET_KEY=
DEBUG=False
USE_SQLITE=False
APP_BASE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_SSLMODE=require
EMAIL_DELIVERY_BACKEND=resend
EMAIL_SEND_ASYNC=True
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=orders@your-verified-domain.com
DEFAULT_FROM_NAME=Savanna Scoops
MPESA_CALLBACK_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}/payments/mpesa/callback/
MPESA_ENVIRONMENT=sandbox
```

Add the Google OAuth and M-Pesa credential variables when you are ready to test those flows.

## Cloudflare

This is a Django application, so it needs a long-running Python server and a persistent database. Do not deploy it directly to Cloudflare Pages as a static site. The practical Cloudflare setup is:

- Django runs on a server, VM, or app host.
- Postgres runs on a managed database provider.
- Cloudflare handles DNS, HTTPS, CDN, WAF, and public routing.
- Cloudflare Tunnel can expose the Django server without opening inbound ports.

### Recommended Production Shape

Use this for a real hosted store:

1. Run Django on a server or app host.
2. Use Postgres, not SQLite.
3. Put the domain on Cloudflare.
4. Route `https://your-domain.com` to the Django origin through Cloudflare DNS or Cloudflare Tunnel.
5. Set `MPESA_CALLBACK_URL` to:

```env
MPESA_CALLBACK_URL=https://your-domain.com/payments/mpesa/callback/
```

Use `.env.cloudflare.example` as the production environment template.

### Cloudflare Tunnel Setup

Cloudflare Tunnel is a good replacement for ngrok when you want a stable Cloudflare hostname.

Requirements:

- A Cloudflare account
- A domain added to Cloudflare
- `cloudflared` installed on the server running Django

In the Cloudflare dashboard:

1. Go to **Zero Trust**.
2. Go to **Networks > Tunnels**.
3. Create a tunnel.
4. Choose the operating system of your server.
5. Copy and run the install command Cloudflare gives you.
6. Add a public hostname:
   - Hostname: `savannascoops.example.com`
   - Service type: `HTTP`
   - Service URL: `localhost:8000`

Then set production environment values:

```env
DEBUG=False
USE_SQLITE=False
ALLOWED_HOSTS=savannascoops.example.com
CSRF_TRUSTED_ORIGINS=https://savannascoops.example.com
MPESA_CALLBACK_URL=https://savannascoops.example.com/payments/mpesa/callback/
```

### Local Test With Cloudflare Tunnel

For a temporary local test, you can run Django locally:

```bash
python manage.py runserver 127.0.0.1:8000
```

Then expose it with a quick tunnel:

```bash
cloudflared tunnel --url http://localhost:8000
```

This gives a temporary Cloudflare URL. Add that hostname to:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,your-temporary-host.trycloudflare.com
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://your-temporary-host.trycloudflare.com
MPESA_CALLBACK_URL=https://your-temporary-host.trycloudflare.com/payments/mpesa/callback/
```

Restart Django after editing `.env`.

### Cloudflare Settings

In Cloudflare SSL/TLS settings, use:

- **Full (strict)** when your origin has a valid TLS certificate.
- **Tunnel-managed routing** when using Cloudflare Tunnel.

Avoid **Flexible** SSL for Django forms and authenticated pages because it can confuse HTTPS detection and secure cookies.

## Render

This project includes:

- `render.yaml`
- `Procfile`
- `build.sh`
- production-ready static file settings
- `DATABASE_URL` support for Postgres

### Deploy steps

1. Create a new GitHub repository and push this project.
2. In Render, create a new Blueprint deployment from the repository.
3. Render will read `render.yaml` and create:
   - a web service
   - a Postgres database
4. In Render, fill in the missing environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `MPESA_CONSUMER_KEY`
   - `MPESA_CONSUMER_SECRET`
   - `MPESA_SHORTCODE`
   - `MPESA_PASSKEY`
   - `MPESA_CALLBACK_URL`
   - `DEFAULT_FROM_EMAIL`
   - `BREVO_API_KEY`
5. Update:
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   with your final Render domain.

### Notes

- The app uses SQLite locally and Postgres automatically when `DATABASE_URL` is present.
- `build.sh` installs dependencies and collects static files during the Render build step.
- Database migrations run in the Render start command.
- Local development keeps using SMTP from `.env`.
- Deployment uses Brevo's SMTP API when `EMAIL_DELIVERY_BACKEND=brevo`.
- Order confirmation emails are queued onto a background thread after payment is committed, so the request can finish without waiting for the email API call.
