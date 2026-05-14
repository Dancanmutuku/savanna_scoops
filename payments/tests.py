import json
from unittest.mock import Mock, patch

from django.test import TestCase
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
    def test_string_success_result_code_marks_order_paid_and_queues_email(self):
        order = Order.objects.create(
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
