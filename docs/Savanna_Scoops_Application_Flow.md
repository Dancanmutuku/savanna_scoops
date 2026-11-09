# Savanna Scoops Application Flow

## 1. Product overview
Savanna Scoops is a Django-based online ice-cream storefront. It has a customer-facing storefront, a cart and checkout flow, an order system, a payment layer for M-Pesa, and a staff/admin dashboard for inventory, fulfillment, and revenue tracking.

The main project entry points are:
- `store/urls.py` → storefront, cart, checkout, tracking, reviews
- `orders/urls.py` → order creation, confirmation, receipt, and status
- `payments/urls.py` → M-Pesa initiation, status checks, callback endpoint
- `inventory/admin_urls.py` / `inventory/views.py` → admin operations
- `savanna_scoops/urls.py` → global routing

## 2. High-level architecture
The app is layered like this:
1. Frontend / Django templates for the customer and admin pages
2. URL routing that dispatches requests to view functions
3. Models for products, cart/session, order lifecycle, payment transactions, and inventory
4. Service logic for M-Pesa integration
5. Database persistence with SQLite (local) or Postgres-like production database
6. Email and analytics work built on model updates and transactional logic

## 3. Customer journey: browsing and buying
### Step 1: Store landing page
A visitor loads `/`.
- `store.views.shop()` loads the catalog from `Flavor` and `Category` models.
- It validates the active catalog, applies category filters and search queries, and renders the shop page.
- Product cards show prices, ratings, and availability.

### Step 2: Product detail / reviews
When the customer clicks a flavor, `flavor_detail()` loads the chosen `Flavor`, related reviews, and suggestions. Users can submit product reviews through `submit_review()`.

### Step 3: Cart behavior
The cart is stored in the user session (`request.session['cart']`), not in the database.
- `add_to_cart()` adds a product and increments quantity.
- `remove_from_cart()` decreases quantity or deletes the item.
- `cart_view()` calculates subtotal, delivery fee, total, and item count.

This is critical: the cart acts as a temporary shopping bag while the user shops.

### Step 4: Checkout page
The customer accesses `/checkout/` via `checkout()`. The view reads the session cart, computes:
- subtotal
- delivery fee (from `SiteSettings`)
- total

The user fills in their name, email, phone, address, and optional instructions. Before placing the order, the app requires an authenticated user.

## 4. Order creation process
When the customer submits checkout:
- `orders/views.py:create_order()` validates the user and cart.
- It creates an `Order` record with customer details, totals, delivery info, and configured payment method.
- It creates one `OrderItem` row per cart item and stores a snapshot of the flavor name, price, quantity, and subtotal.
- It logs an initial `OrderStatusHistory` with status `pending` and note `Order created, awaiting payment.`
- It saves `pending_order_id` in the session.

Key model: `orders.models.Order`
- `status` values: pending → confirmed → preparing → out_for_delivery → delivered / cancelled
- `payment_status` values: pending / paid / cancelled
- `order_number` is generated as `SS-<random>` and unique.

## 5. Payment flow: M-Pesa STK Push
The payment flow is handled by the `payments` app.

### Step 1: Customer initiates payment
The frontend sends a POST request to `/payments/mpesa/initiate/`.
- `payments.views.initiate_mpesa()` reads `phone` and `order_id`.
- It verifies the order belongs to the logged-in user and is not already paid.
- It calls `payments.mpesa.initiate_stk_push()`.

### Step 2: Generate access token
`get_mpesa_access_token()`:
- Builds the Daraja OAuth URL
- Uses `MPESA_CONSUMER_KEY` + `MPESA_CONSUMER_SECRET`
- Encodes as Basic Auth
- Requests `access_token` from Safaricom

### Step 3: Build STK push payload
`get_stk_password()` creates the required password using:
- business shortcode
- passkey
- current timestamp

`initiate_stk_push()` then sends a POST to Safaricom STK Push API with:
- `BusinessShortCode`
- `Password`
- `Timestamp`
- `TransactionType`
- `Amount`
- `PartyA` (customer phone)
- `PartyB` (merchant shortcode)
- `CallBackURL` (`MPESA_CALLBACK_URL`)
- `AccountReference`
- `TransactionDesc`

If the request succeeds, Safaricom returns:
- `CheckoutRequestID`
- `MerchantRequestID`
- `ResponseCode`
- `CustomerMessage`

### Step 4: Record transaction in DB
The app creates a `MpesaTransaction` record with:
- order reference
- merchant request ID
- checkout request ID
- phone number
- amount
- status = pending

This gives the app a durable record to reconcile with Safaricom callbacks and reconciliation checks.

## 6. Payment confirmation loop
There are two confirmation mechanisms.

### A. Check payment status endpoint
`payments.views.check_payment_status()`:
- finds the `MpesaTransaction` by `checkout_request_id`
- verifies the logged-in user is allowed to access it
- checks local DB first if already success/cancelled/failed
- otherwise calls `query_stk_status(checkout_request_id)` from `payments/mpesa.py`
- interprets `ResultCode` and decides whether payment is:
  - success
  - cancelled
  - still pending

If success, it calls `_mark_order_paid()`, which:
- updates order `payment_status` to `paid`
- sets `payment_method = 'M-Pesa'`
- sets `status = 'confirmed'`
- stores `mpesa_receipt`
- creates an `OrderStatusHistory` row
- triggers `queue_order_confirmation_email(order.id)` on database commit

### B. Safaricom callback endpoint
`payments.views.mpesa_callback()` is the main reliability path.
- It is a CSRF-exempt POST endpoint at `/payments/mpesa/callback/`
- Safaricom calls it after the STK prompt result is available.
- It validates callback token and extracts `CheckoutRequestID`, `MerchantRequestID`, `ResultCode`, `ResultDesc`.
- It looks up the associated `MpesaTransaction`.
- It verifies the callback metadata contains:
  - `MpesaReceiptNumber`
  - `Amount`
- It ensures the amount paid matches the order total.

If valid, it updates the transaction to `success` and marks the order as paid. If the user cancels, result code `1032` is handled as `cancelled`. Other failure codes are recorded as failed/pending without immediately canceling the order.

## 7. Manual payment flow
Not all orders are M-Pesa.
- `complete_manual_payment()` allows staff to mark an order paid with a non-M-Pesa method like cash, card, or bank transfer.
- It uses `_mark_order_paid()` to update the order and send the confirmation email.

## 8. Order status lifecycle and fulfillment
After payment is confirmed, the order moves through workflow stages:
- `confirmed`
- `preparing`
- `out_for_delivery`
- `delivered`

Staff can update status through `inventory.views.update_order_status()` from the admin operations panel. Each update produces an `OrderStatusHistory` record for auditability.

## 9. Inventory and admin operations
The admin panel (`/admin-panel/`) is a staff-only interface.
- `admin_dashboard()` shows today’s revenue, revenue trend, active orders, low stock count, recent transactions, top flavors, and analytics data.
- `inventory_list()` lists inventory items and highlights low-stock items.
- `inventory_update()` allows stock adjustments and logs a `StockMovement` and `AuditLog` entry.
- `orders_admin()` lists orders with status filters.
- `analytics_view()` summarizes sales trends and live customer activity.

## 10. Security and business logic safeguards
The app contains several protections:
- login required for checkout and order tracking
- staff-only guards for admin pages
- callback token validation for M-Pesa notifications
- amount verification against order total before accepting a callback
- duplicate callback protection
- transaction atomicity for order payment updates
- customer ownership checks before exposing payment details

## 11. End-to-end summary
A complete flow looks like this:
1. Customer visits the shop, picks items, and adds them to the session cart.
2. Customer logs in and lands on checkout.
3. Order is created in the database with totals and customer data.
4. Customer starts M-Pesa STK Push.
5. Safaricom sends a payment prompt to the customer’s phone.
6. Safaricom calls the callback URL with the result.
7. App validates the callback payload, receipt, and amount.
8. Order is marked as paid and status updates to confirmed.
9. Staff can process the order in the admin dashboard.
10. Customer sees order confirmation/receipt and can check order status.

## 12. Key files to inspect
- `store/views.py` — cart, catalog, checkout
- `orders/views.py` — order creation/confirmation/status APIs
- `payments/mpesa.py` — Daraja integration helpers
- `payments/views.py` — STK initiation, status checking, callback handling
- `orders/models.py` — order lifecycle data
- `payments/models.py` — transaction record model
- `inventory/views.py` — staff operations and analytics

## 13. Operational notes
For local testing, set `MPESA_CALLBACK_URL` to an ngrok URL and ensure the host is allowed in Django settings. This is important because M-Pesa requires a public HTTPS endpoint to reach the local environment.
