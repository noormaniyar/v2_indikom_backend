# IndiKom Backend
### Django REST API — E-Commerce Platform (Amazon/Flipkart-like)

---

## 📋 Project Structure

```
indikom_backend/
├── config/
│   ├── settings.py          # All settings, env-driven
│   ├── urls.py              # Root URL dispatcher
│   ├── celery.py            # Celery app config
│   ├── pagination.py        # Standard paginator
│   └── wsgi.py
│
├── apps/
│   ├── accounts/            # User, SupplierProfile, DeliveryAgent, OTP, Address
│   ├── products/            # Category (MPTT tree), SubCategory, Product,
│   │   │                    #   Variants, Images, Specs, Cart, Wishlist, Reviews
│   │   └── management/
│   │       └── commands/
│   │           └── seed_data.py   # Seeds categories + attributes + plans
│   │
│   ├── orders/              # Order, OrderItem, Coupon, ReturnRequest
│   ├── payments/            # Payment (Razorpay + Stripe + COD), SavedCard
│   ├── delivery/            # Shipment, ShipmentTracking
│   ├── subscriptions/       # SupplierSubscription, SubscriptionPlan
│   ├── moderator/           # Dashboard + moderation views (no extra models)
│   ├── notifications/       # Notification model + views
│   ├── tasks.py             # Celery async tasks (SMS, email, notifications)
│   └── utils.py             # Shared helpers
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── API_REFERENCE.md         # Full endpoint table with payloads
```

---

## 🚀 Quick Start

### Option A — Local (virtualenv)

```bash
# 1. Clone & create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — at minimum set DB_NAME, DB_USER, DB_PASSWORD

# 4. Create database (PostgreSQL)
createdb indikom_db

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Seed initial data (categories, attributes, subscription plans)
python manage.py seed_data

# 7. Create admin superuser
python manage.py createsuperuser

# 8. Start the server
python manage.py runserver
```

### Option B — Docker Compose

```bash
cp .env.example .env
docker-compose up --build

# In a second terminal:
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py createsuperuser
```

---

## 🌐 URLs After Setup

| URL | Description |
|-----|-------------|
| http://localhost:8000/admin/ | Django Admin panel |
| http://localhost:8000/api/docs/ | Swagger UI (interactive) |
| http://localhost:8000/api/redoc/ | ReDoc API docs |
| http://localhost:8000/api/v1/ | REST API root |

---

## 🏗️ Key Design Decisions

### 1. Your Models — Preserved Exactly
Your existing `Category`, `SubCategory`, and `Product` models are kept **unchanged**.  
We added:
- `Category.parent` (MPTT) for unlimited nesting — old FKs still work
- `Product.slug`, `.discount_price`, `.rating`, `.moderation_status`, `.has_ar`, etc.

### 2. Unlimited Category Depth (Amazon/Flipkart style)
Uses **django-mptt** — stores tree in adjacency list with `lft/rght/level/tree_id`
for `O(1)` ancestor/descendant queries.

```
Appliances (level 0)
  └── Kitchen (level 1)
        └── Toaster (level 2)
              └── 2-Slice Popup Toaster (level 3)
```

### 3. Multi-Level Product Variants
A `ProductVariant` has multiple `VariantAttribute` rows — one per axis:

```
Product: Nordic Sofa
  Variant 1: [Size=3-Seater] [Color=Light Grey] [Material=Wool]   SKU: SOFA-3S-LG-W
  Variant 2: [Size=2-Seater] [Color=Coffee Brown] [Material=Linen] SKU: SOFA-2S-CB-L
```

Each variant has its own price, stock, SKU, and thumbnail.

### 4. AR Preview Integration
- Upload `.glb` (Android) or `.usdz` (iOS) as `Product.ar_file`
- `has_ar=True` is auto-set on save
- Flutter uses `model_viewer_plus` package:

```dart
ModelViewer(
  src: product.arFileUrl,
  ar: true,
  autoRotate: true,
)
```

### 5. Multi-Supplier Order Flow
```
Customer → Place Order (cart items from Supplier A + B)
    ↓
Order created → OrderItems each have supplier FK + item_status
    ↓
Supplier A sees their items only → updates item_status
Supplier B sees their items only → updates item_status
    ↓
Moderator/Admin creates Shipment → assigns Delivery Agent
    ↓
Agent updates Shipment.status → ShipmentTracking events created
    ↓
Order marked DELIVERED → notification sent to customer
```

### 6. Payment Flow (Razorpay)
```
POST /payments/initiate/  →  razorpay_order_id returned
Flutter: opens Razorpay SDK checkout
POST /payments/verify/razorpay/  →  HMAC signature verified
Order.payment_status = PAID, Order.status = CONFIRMED
```

---

## 👥 User Roles

| Role | Can Do |
|------|--------|
| `customer` | Browse, cart, orders, reviews, wishlist |
| `supplier` | Upload products, manage variants, see own orders |
| `moderator` | Approve suppliers/products, update order status |
| `delivery_agent` | See assigned shipments, update delivery status |
| `admin` | Everything + user management |

---

## 🔑 Auth Flow (Flutter Integration)

```dart
// 1. Register
POST /api/v1/auth/register/
→ { tokens: { access, refresh }, user: {...} }

// 2. Store tokens in Flutter secure storage
FlutterSecureStorage().write(key: 'access_token', value: tokens.access)

// 3. All subsequent requests
headers: { 'Authorization': 'Bearer $accessToken' }

// 4. Refresh when 401
POST /api/v1/auth/token/refresh/
body: { "refresh": "$refreshToken" }

// 5. OTP phone verification
POST /api/v1/auth/otp/request/  →  SMS sent
POST /api/v1/auth/otp/verify/   →  verified
```

---

## ⚡ Celery Async Tasks

```bash
# Start worker
celery -A config worker -l info

# Start beat (periodic tasks)
celery -A config beat -l info
```

Tasks defined in `apps/tasks.py`:
- `send_otp_sms_task` — Send OTP via SMS provider
- `send_order_email_task` — Order confirmation email
- `send_supplier_approval_task` — Supplier status email
- `create_order_notification_task` — In-app notification
- `update_product_rating_task` — Recalculate product rating
- `expire_unpaid_orders_task` — Cancel stale unpaid orders (runs every 15 min)

---

## 🔧 Admin Actions Available

| Section | Action |
|---------|--------|
| Users | Activate/deactivate accounts |
| Suppliers | Approve / Reject / Suspend |
| Products | Approve / Reject / Mark Featured |
| Orders | Update status |
| Reviews | Approve reviews |
| Coupons | Create/deactivate |

---

## 📦 Flutter Integration Checklist

- [ ] Install `dio` + `flutter_secure_storage` for auth
- [ ] Install `razorpay_flutter` for payments
- [ ] Install `model_viewer_plus` for AR preview
- [ ] Set `BASE_URL` to your backend IP/domain
- [ ] Add `ACCESS_TOKEN` to every request header
- [ ] Handle 401 → refresh token flow
- [ ] Use `multipart/form-data` for product image uploads

---

## 🛠️ Environment Variables Reference

See `.env.example` for full list. Key variables:

```ini
SECRET_KEY=          # Django secret key
DEBUG=True           # Set False in production
DB_NAME=indikom_db
DB_USER=postgres
DB_PASSWORD=postgres
REDIS_URL=redis://localhost:6379/0
RAZORPAY_KEY_ID=     # From Razorpay dashboard
RAZORPAY_KEY_SECRET= # From Razorpay dashboard
```
