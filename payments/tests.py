import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order

from .models import MpesaTransaction
from .mpesa import get_mpesa_access_token


class MpesaClientTests(TestCase):
    @patch('payments.mpesa.requests.get')
    def test_access_token_returns_none_for_non_json_response(self, mock_get):
        response = Mock(status_code=502, text='')
        response.json.side_effect = ValueError('No JSON')
        mock_get.return_value = response

        self.assertIsNone(get_mpesa_access_token())


class MpesaStatusTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_string_success_result_code_marks_order_paid_and_queues_email(self):
        user = User.objects.create_user(username='jane@example.com', email='jane@example.com', password='pass12345')
        self.client.force_login(user)
        order = Order.objects.create(
            user=user,
            customer_name='Jane Customer',
            customer_email='jane@example.com',
            customer_phone='+254712345678',
            delivery_address='Nairobi',
            subtotal=500,
            delivery_fee=150,
            total=650,
            payment_method='M-Pesa',
        )
        MpesaTransaction.objects.create(
            order=order,
            merchant_request_id='merchant-1',
            checkout_request_id='checkout-1',
            phone_number='+254712345678',
            amount=650,
            status='pending',
        )

        with patch('payments.views.query_stk_status', return_value={'ResultCode': '0'}), \
                patch('payments.views.queue_order_confirmation_email') as mock_queue, \
                self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('check_payment_status'),
                data=json.dumps({'checkout_request_id': 'checkout-1'}),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.status, 'confirmed')
        mock_queue.assert_called_once_with(order.id)

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_mpesa_callback_handles_single_dict_metadata_item(self):
        user = User.objects.create_user(username='jack@example.com', email='jack@example.com', password='pass12345')
        self.client.force_login(user)
        order = Order.objects.create(
            user=user,
            customer_name='Jack Customer',
            customer_email='jack@example.com',
            customer_phone='+254712345678',
            delivery_address='Nairobi',
            subtotal=500,
            delivery_fee=150,
            total=650,
            payment_method='M-Pesa',
        )
        txn = MpesaTransaction.objects.create(
            order=order,
            merchant_request_id='merchant-2',
            checkout_request_id='checkout-2',
            phone_number='+254712345678',
            amount=650,
            status='pending',
        )

        payload = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': 'merchant-2',
                    'CheckoutRequestID': 'checkout-2',
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully.',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 650.0},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'QJABC123'},
                        ]
                    }
                }
            }
        }

        response = self.client.post(
            reverse('mpesa_callback'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'success')
        self.assertEqual(txn.mpesa_receipt_number, 'QJABC123')
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
