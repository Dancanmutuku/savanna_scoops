# Savanna Scoops Deployment

## Production setup

Use a standard Django production setup with a hosted PostgreSQL database and an external email provider if you want transactional mail.

### Recommended environment values

```env
DEBUG=False
USE_SQLITE=False
DATABASE_URL=postgresql://user:password@host:5432/database
DATABASE_SSLMODE=require
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
APP_BASE_URL=https://your-domain.com
MPESA_CALLBACK_URL=https://your-domain.com/payments/mpesa/callback/
```

Keep `DATABASE_URL` and any secrets in your host environment or a secrets manager. Do not commit `.env` files to source control.

## Deploying to a modern host

Any standard Python host is fine, including:

- Azure App Service
- Render
- Heroku-style PaaS providers
- a VPS running Gunicorn + Nginx

Use the project as a normal Django app and ensure that:

- `USE_SQLITE=False` when using PostgreSQL
- `DEBUG=False` in production
- `ALLOWED_HOSTS` includes the live domain
- `CSRF_TRUSTED_ORIGINS` includes the HTTPS origin used by the app

## Email configuration

The app supports SMTP by default and Brevo when `EMAIL_DELIVERY_BACKEND=brevo` together with a valid `BREVO_API_KEY`.

```env
EMAIL_DELIVERY_BACKEND=brevo
EMAIL_SEND_ASYNC=True
BREVO_API_KEY=your-brevo-key
BREVO_API_URL=https://api.brevo.com/v3/smtp/email
DEFAULT_FROM_NAME=Savanna Scoops
DEFAULT_FROM_EMAIL=orders@your-domain.com
```

## GitHub

1. Push the project to a GitHub repository.
2. Keep `.env` out of the repository.
3. Use your host or CI environment for runtime secrets.
