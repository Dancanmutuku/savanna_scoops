import requests
import base64
from datetime import datetime
from django.conf import settings


def get_mpesa_access_token():
    """Get M-Pesa OAuth access token."""
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    credentials = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()
    
    response = requests.get(
        url,
        headers={'Authorization': f'Basic {credentials}'},
        timeout=10
    )
    return response.json().get('access_token')


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
        data = response.json()
        
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
        return response.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}
