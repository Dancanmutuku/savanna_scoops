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
