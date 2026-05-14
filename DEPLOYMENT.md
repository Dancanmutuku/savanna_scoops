# Savanna Scoops Deployment

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
