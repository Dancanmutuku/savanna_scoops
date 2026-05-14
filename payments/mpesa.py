import requests
import base64
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def _safe_json_response(response, context):
    try:
        return response.json()
    except ValueError:
        logger.warning(
            "M-Pesa %s returned non-JSON response. Status: %s, Body: %r",
            context,
            response.status_code,
            response.text[:500],
        )
        return None


def get_mpesa_access_token():
    """Get M-Pesa OAuth access token."""
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    credentials = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()
    
    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Basic {credentials}'},
            timeout=10
        )
        data = _safe_json_response(response, 'token request')
        if not data:
            return None

        if response.status_code >= 400:
            logger.warning(
                "M-Pesa token request failed. Status: %s, Response: %s",
                response.status_code,
                data,
            )
            return None

        token = data.get('access_token')
        if not token:
            logger.warning("M-Pesa token response did not include access_token: %s", data)
        return token
    except requests.exceptions.RequestException:
        logger.exception("M-Pesa token request failed.")
        return None


def get_stk_password():
    """Generate STK Push password."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def initiate_stk_push(phone_number: str, amount: float, order_number: str, account_ref: str = None):
    """
    Initiate M-Pesa STK Push.
    Returns: dict with success status and checkout_request_id
    """
    # Normalize phone number to 254...
    phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        phone = '254' + phone
    
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'success': False, 'error': 'Could not get access token'}
    
    password, timestamp = get_stk_password()
    
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    else:
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone,
        'PartyB': settings.MPESA_SHORTCODE,
        'PhoneNumber': phone,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': account_ref or order_number,
        'TransactionDesc': f'Savanna Scoops - {order_number}',
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            timeout=30
        )
        data = _safe_json_response(response, 'STK push request')
        if data is None:
            return {'success': False, 'error': 'M-Pesa returned an invalid response'}
        
        if data.get('ResponseCode') == '0':
            return {
                'success': True,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'response_code': data.get('ResponseCode'),
                'customer_message': data.get('CustomerMessage'),
            }
        else:
            return {
                'success': False,
                'error': data.get('errorMessage', 'STK push failed'),
                'data': data,
            }
    except requests.exceptions.RequestException as e:
        logger.exception("M-Pesa STK push request failed.")
        return {'success': False, 'error': str(e)}


def query_stk_status(checkout_request_id: str):
    """Query the status of an STK push request."""
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'success': False, 'error': 'Could not get access token'}
    
    password, timestamp = get_stk_password()
    
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    else:
        url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=15
        )
        data = _safe_json_response(response, 'STK status query')
        if data is None:
            return {
                'success': False,
                'status': 'pending',
                'error': 'M-Pesa returned an invalid response',
            }
        return data
    except requests.exceptions.RequestException as e:
        logger.exception("M-Pesa STK status query failed.")
        return {'success': False, 'error': str(e)}
