import base64
import logging
from datetime import datetime

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _safe_json_response(response, context):
    """
    Safely parse a Safaricom response as JSON.

    Safaricom may occasionally return an HTML response
    instead of JSON, especially when an upstream security
    layer rejects the request.
    """
    try:
        return response.json()
    except ValueError:
        logger.warning(
            "M-Pesa %s returned non-JSON response. "
            "HTTP %s. Body: %r",
            context,
            response.status_code,
            response.text[:500],
        )
        return None


def _mpesa_base_url():
    """
    Return the correct Daraja API base URL.
    """
    environment = getattr(
        settings,
        "MPESA_ENVIRONMENT",
        "sandbox",
    ).lower().strip()

    if environment == "production":
        return "https://api.safaricom.co.ke"

    return "https://sandbox.safaricom.co.ke"


def get_mpesa_access_token():
    """
    Get an OAuth access token from Safaricom Daraja.
    """

    url = (
        f"{_mpesa_base_url()}"
        "/oauth/v1/generate"
        "?grant_type=client_credentials"
    )

    consumer_key = getattr(
        settings,
        "MPESA_CONSUMER_KEY",
        "",
    )

    consumer_secret = getattr(
        settings,
        "MPESA_CONSUMER_SECRET",
        "",
    )

    if not consumer_key or not consumer_secret:
        logger.error(
            "M-Pesa consumer credentials are not configured."
        )
        return None

    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode("utf-8")
    ).decode("ascii")

    headers = {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json",
        "User-Agent": "SavannaScoops/1.0",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
        )

        data = _safe_json_response(
            response,
            "token request",
        )

        if response.status_code != 200:
            logger.error(
                "M-Pesa token request failed. "
                "HTTP status: %s. Response: %s",
                response.status_code,
                data if data is not None else response.text[:500],
            )
            return None

        if not data:
            logger.error(
                "M-Pesa token request returned an empty response."
            )
            return None

        token = data.get("access_token")

        if not token:
            logger.error(
                "M-Pesa token response did not contain access_token: %s",
                data,
            )
            return None

        return token

    except requests.exceptions.Timeout:
        logger.error(
            "M-Pesa token request timed out."
        )
        return None

    except requests.exceptions.RequestException:
        logger.exception(
            "M-Pesa token request failed."
        )
        return None


def get_stk_password():
    """
    Generate the password required for STK Push / STK Query.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    raw = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        raw.encode("utf-8")
    ).decode("ascii")

    return password, timestamp


def normalize_mpesa_phone(phone_number):
    """
    Convert Kenyan phone numbers to 254XXXXXXXXX format.
    """

    phone = (
        str(phone_number or "")
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if phone.startswith("0"):
        phone = "254" + phone[1:]

    elif phone.startswith("7") or phone.startswith("1"):
        phone = "254" + phone

    return phone


def initiate_stk_push(
    phone_number: str,
    amount: float,
    order_number: str,
    account_ref: str = None,
):
    """
    Initiate an M-Pesa STK Push.
    """

    phone = normalize_mpesa_phone(phone_number)

    if not phone:
        return {
            "success": False,
            "error": "Invalid phone number.",
        }

    try:
        amount = int(float(amount))
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Invalid payment amount.",
        }

    access_token = get_mpesa_access_token()

    if not access_token:
        return {
            "success": False,
            "error": (
                "Unable to connect to M-Pesa. "
                "Please try again later."
            ),
        }

    password, timestamp = get_stk_password()

    url = (
        f"{_mpesa_base_url()}"
        "/mpesa/stkpush/v1/processrequest"
    )

    callback_url = getattr(
        settings,
        "MPESA_CALLBACK_URL",
        "",
    )

    if not callback_url:
        logger.error(
            "MPESA_CALLBACK_URL is not configured."
        )

        return {
            "success": False,
            "error": "M-Pesa callback URL is not configured.",
        }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_ref or order_number,
        "TransactionDesc": (
            f"Savanna Scoops - {order_number}"
        ),
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SavannaScoops/1.0",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        data = _safe_json_response(
            response,
            "STK push request",
        )

        if response.status_code >= 400:
            logger.error(
                "M-Pesa STK push failed. "
                "HTTP %s. Response: %s",
                response.status_code,
                data if data is not None else response.text[:500],
            )

            return {
                "success": False,
                "error": (
                    data.get("errorMessage")
                    if data
                    else "M-Pesa rejected the request."
                ),
            }

        if not data:
            return {
                "success": False,
                "error": "M-Pesa returned an invalid response.",
            }

        if data.get("ResponseCode") == "0":
            return {
                "success": True,
                "checkout_request_id": data.get(
                    "CheckoutRequestID"
                ),
                "merchant_request_id": data.get(
                    "MerchantRequestID"
                ),
                "response_code": data.get(
                    "ResponseCode"
                ),
                "customer_message": data.get(
                    "CustomerMessage"
                ),
            }

        return {
            "success": False,
            "error": data.get(
                "errorMessage",
                "STK Push failed.",
            ),
            "data": data,
        }

    except requests.exceptions.Timeout:
        logger.error(
            "M-Pesa STK Push request timed out."
        )

        return {
            "success": False,
            "error": "M-Pesa request timed out.",
        }

    except requests.exceptions.RequestException as exc:
        logger.exception(
            "M-Pesa STK Push request failed."
        )

        return {
            "success": False,
            "error": str(exc),
        }


def query_stk_status(checkout_request_id: str):
    """
    Query the status of an M-Pesa STK Push.
    """

    if not checkout_request_id:
        return {
            "success": False,
            "error": "Checkout request ID is required.",
        }

    access_token = get_mpesa_access_token()

    if not access_token:
        return {
            "success": False,
            "status": "unavailable",
            "error": (
                "Unable to obtain M-Pesa access token."
            ),
        }

    password, timestamp = get_stk_password()

    url = (
        f"{_mpesa_base_url()}"
        "/mpesa/stkpushquery/v1/query"
    )

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SavannaScoops/1.0",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15,
        )

        data = _safe_json_response(
            response,
            "STK status query",
        )

        if response.status_code >= 400:
            logger.error(
                "M-Pesa STK status query failed. "
                "HTTP %s. Response: %s",
                response.status_code,
                data if data is not None else response.text[:500],
            )

            return {
                "success": False,
                "status": "unavailable",
                "error": (
                    "M-Pesa status service is temporarily unavailable."
                ),
            }

        if not data:
            return {
                "success": False,
                "status": "unavailable",
                "error": "M-Pesa returned an invalid response.",
            }

        return data

    except requests.exceptions.Timeout:
        logger.error(
            "M-Pesa STK status query timed out."
        )

        return {
            "success": False,
            "status": "unavailable",
            "error": "M-Pesa status query timed out.",
        }

    except requests.exceptions.RequestException as exc:
        logger.exception(
            "M-Pesa STK status query failed."
        )

        return {
            "success": False,
            "status": "unavailable",
            "error": str(exc),
        }