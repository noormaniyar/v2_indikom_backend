# IndiKom Backend — Complete API Reference

**Base URL:** `http://localhost:8000/api/v1/`  
**Auth:** Bearer JWT token in `Authorization` header  
**Docs:** `http://localhost:8000/api/docs/` (Swagger UI)

---

## 🔐 AUTH — `/api/v1/auth/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `register/` | ❌ | Register customer or supplier |
| POST | `login/` | ❌ | Login → returns access + refresh tokens |
| POST | `logout/` | ✅ | Blacklist refresh token |
| POST | `token/refresh/` | ❌ | Refresh access token |
| GET/PUT | `me/` | ✅ | Get/update own profile |
| POST | `me/change-password/` | ✅ | Change password |
| POST | `otp/request/` | ❌ | Send OTP to phone |
| POST | `otp/verify/` | ❌ | Verify OTP |
| POST | `forgot-password/` | ❌ | Send reset OTP to email |
| POST | `reset-password/` | ❌ | Reset password with OTP |
| GET/POST | `addresses/` | ✅ | List / create addresses |
| GET/PUT/DELETE | `addresses/<id>/` | ✅ | Manage address |
| POST | `addresses/<id>/set-default/` | ✅ | Set default address |
| GET/PUT | `supplier/profile/` | ✅ Supplier | View/update supplier profile |
| GET/PUT | `delivery/profile/` | ✅ Agent | View/update agent profile |

### Register payload
```json
{
  "email": "user@example.com",
  "phone": "+919876543210",
  "first_name": "Alex",
  "last_name": "Mason",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "role": "customer"  // or "supplier"
}
```

### Login response
```json
{
  "tokens": { "access": "...", "refresh": "..." },
  "user": { "id": 1, "email": "...", "role": "customer", "full_name": "Alex Mason" }
}
```

---

## 📦 PRODUCTS — `/api/v1/products/`

### Public Endpoints (no auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `categories/tree/` | Full nested category tree |
| GET | `categories/` | Flat list, filter by `?parent=null` or `?parent=<id>` |
| GET | `categories/<slug>/` | Category detail with children |
| GET | `subcategories/` | List subcategories, filter by `?category=<slug>` |
| GET | `attributes/` | Variant attribute definitions, filter by `?category=<slug>` |
| GET | `` (root) | Product list with filters |
| GET | `featured/` | Featured products |
| GET | `<slug>/` | Product detail page |
| GET | `<slug>/reviews/` | Product reviews |

### Product List Filters
```
GET /api/v1/products/?
  category=appliances          # category slug
  sub_category=kitchen         # sub-category slug
  min_price=100
  max_price=5000
  brand=samsung
  min_rating=4
  has_discount=true
  has_ar=true
  in_stock=true
  is_featured=true
  search=toaster               # searches name, brand, tags, description
  ordering=price               # or -price, rating, created_at
  page=1
  page_size=20
```

### Customer Authenticated

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `wishlist/` | View wishlist / add item |
| DELETE | `wishlist/<id>/` | Remove from wishlist |
| POST | `wishlist/toggle/<product_id>/` | Toggle wishlist |
| GET | `cart/` | View cart with totals |
| POST | `cart/add/` | Add item to cart |
| PUT/DELETE | `cart/items/<id>/` | Update quantity / remove |
| DELETE | `cart/clear/` | Clear cart |
| POST | `<slug>/reviews/` | Submit review |

### Cart Add payload
```json
{
  "product_id": 5,
  "variant_id": 12,   // optional
  "quantity": 2
}
```

### Supplier Endpoints (approved supplier only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `supplier/products/` | List/create own products |
| GET/PUT/DELETE | `supplier/products/<id>/` | Manage product |
| GET/POST | `supplier/products/<id>/images/` | Upload product images |
| DELETE | `supplier/images/<id>/` | Delete image |
| GET/POST | `supplier/products/<id>/variants/` | List/create variants |
| PUT/DELETE | `supplier/variants/<id>/` | Manage variant |

### Product Upload Form payload (multipart/form-data)
```json
{
  "name": "Nordic Lounge Sofa",
  "category": 3,
  "sub_category": 7,
  "brand": "IndiKom",
  "sku": "SOFA-NORDIC-001",
  "description": "Minimalist Scandinavian design...",
  "price": "1199.00",
  "discount_price": "899.00",
  "stock": 50,
  "weight": "35.5",
  "dimensions": "210 x 85 x 75",
  "thumbnail": <file>,
  "ar_file": <glb/usdz file>,
  "tags": "sofa,nordic,living room,3-seater",
  "specifications": [
    {"key": "Material", "value": "Linen", "unit": ""},
    {"key": "Seating", "value": "3", "unit": "persons"},
    {"key": "Frame", "value": "Solid Oak", "unit": ""}
  ]
}
```

### Variant Create payload
```json
{
  "sku": "SOFA-NORDIC-3S-LG",
  "price": null,           // null = inherit from product
  "discount_price": null,
  "stock": 20,
  "thumbnail": <file>,
  "attributes": [
    {"attribute_id": 1, "value_id": 5},   // Size: 3-Seater
    {"attribute_id": 2, "value_id": 12},  // Color: Light Grey
    {"attribute_id": 3, "value_id": 18}   // Material: Wool
  ]
}
```

---

## 🛍️ ORDERS — `/api/v1/orders/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `place/` | ✅ Customer | Place order from cart |
| GET | `` | ✅ Customer | My order list |
| GET | `<order_id>/` | ✅ Customer | Order detail (e.g. `PR9921`) |
| POST | `<order_id>/cancel/` | ✅ Customer | Cancel order |
| POST | `coupons/validate/` | ✅ | Validate coupon code |
| GET/POST | `returns/` | ✅ Customer | View / create return requests |
| GET | `supplier/orders/` | ✅ Supplier | Orders containing my products |
| PATCH | `supplier/items/<id>/status/` | ✅ Supplier | Update item fulfilment status |
| GET | `admin/orders/` | ✅ Moderator | All orders |
| PATCH | `admin/orders/<order_id>/` | ✅ Moderator | Update order status |

### Place Order payload
```json
{
  "address_id": 3,
  "coupon_code": "SAVE20",
  "notes": "Please ring the bell",
  "payment_method": "razorpay"  // razorpay | stripe | cod | upi
}
```

### Place Order response
```json
{
  "message": "Order placed successfully.",
  "order": {
    "order_id": "PR9921100",
    "status": "pending",
    "subtotal": "1649.00",
    "discount_amount": "300.00",
    "tax_amount": "131.92",
    "total_amount": "1780.92",
    "items": [...]
  },
  "payment_required": true,
  "payment_method": "razorpay"
}
```

---

## 💳 PAYMENTS — `/api/v1/payments/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `initiate/` | ✅ | Create gateway order/intent |
| POST | `verify/razorpay/` | ✅ | Verify Razorpay payment signature |
| GET | `<id>/` | ✅ | Payment detail |

### Initiate Payment
```json
{
  "order_id": "PR9921100",
  "method": "razorpay"
}
```
Response includes `razorpay_order_id` and `key_id` for Flutter Razorpay SDK.

### Verify Razorpay
```json
{
  "razorpay_order_id": "order_xxx",
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "abc123..."
}
```

---

## 🚚 DELIVERY — `/api/v1/delivery/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `track/<tracking_id>/` | ❌ | Public shipment tracking |
| GET | `order/<order_id>/` | ✅ Customer | Track my order |
| GET | `agent/shipments/` | ✅ Agent | Active assigned shipments |
| PATCH | `agent/shipments/<id>/update/` | ✅ Agent | Update delivery status + GPS |
| POST | `admin/create/` | ✅ Moderator | Create shipment & assign agent |

### Agent Status Update
```json
{
  "status": "out_for_delivery",
  "location": "MG Road, Pune",
  "description": "Package picked up from hub",
  "latitude": "18.5204",
  "longitude": "73.8567"
}
```

---

## 📋 SUBSCRIPTIONS — `/api/v1/subscriptions/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `plans/` | ❌ | Available supplier plans |
| GET | `my/` | ✅ Supplier | My subscriptions |
| POST | `subscribe/` | ✅ Supplier | Subscribe to a plan |

---

## 🛡️ MODERATOR — `/api/v1/moderator/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `dashboard/` | ✅ Mod | Stats: users, orders, revenue |
| GET | `suppliers/` | ✅ Mod | Supplier list `?status=pending` |
| POST | `suppliers/<id>/moderate/` | ✅ Mod | Approve/Reject/Suspend supplier |
| GET | `products/` | ✅ Mod | Product list `?status=pending` |
| POST | `products/<id>/moderate/` | ✅ Mod | Approve/Reject product |
| POST | `products/<id>/feature/` | ✅ Mod | Toggle featured |
| GET | `users/` | ✅ Mod | All users `?role=supplier` |
| POST | `users/<id>/toggle-active/` | ✅ Admin | Activate/Deactivate user |

---

## 🔔 NOTIFICATIONS — `/api/v1/notifications/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `` | My notifications |
| GET | `unread-count/` | `{ "unread_count": 5 }` |
| POST | `mark-read/` | Mark all as read |
| POST | `<id>/mark-read/` | Mark single as read |

---

## 🏗️ Architecture Notes

### Category System (unlimited depth like Amazon/Flipkart)
- Uses **django-mptt** for efficient tree storage
- Example tree: `Appliances > Kitchen > Toaster > 2-Slice`
- Query children: `GET /categories/?parent=<id>`
- Full nested tree: `GET /categories/tree/`
- Old `Category` → `SubCategory` FK preserved for backward compatibility

### Multi-Level Variants
- `ProductVariant` has many `VariantAttribute` rows (one per dimension)
- Example: `3-Seater / Light Grey / Wool` = 3 VariantAttribute rows
- Each variant has own price, stock, SKU, image

### AR Preview
- Upload `.glb` (Android) or `.usdz` (iOS) as `ar_file`
- Flutter uses `model_viewer_plus` package to render 3D AR
- `has_ar` flag auto-set when `ar_file` is present

### Multi-Supplier Orders
- Single order can contain items from multiple suppliers
- Each `OrderItem` has its own `supplier` FK and `item_status`
- Suppliers see only their items; `SupplierOrderListView` filters accordingly

### Payment Flow (Razorpay)
1. `POST /payments/initiate/` → get `razorpay_order_id`
2. Flutter opens Razorpay checkout
3. `POST /payments/verify/razorpay/` → signature verification → order confirmed

---

## 🚀 Setup & Run

```bash
# 1. Clone and setup
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py makemigrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Load initial data (optional)
python manage.py loaddata fixtures/initial_categories.json

# 6. Run server
python manage.py runserver

# OR with Docker
docker-compose up --build
```

Admin panel: `http://localhost:8000/admin/`  
Swagger docs: `http://localhost:8000/api/docs/`
