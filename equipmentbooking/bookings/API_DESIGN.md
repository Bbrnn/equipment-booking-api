# Equipment Booking API — System & API Design Document

## 1. Overview & Architecture

The **Equipment Booking API** is a RESTful backend service built with Django and Django REST Framework (DRF). It enables organizations to track shared equipment inventory, browse availability across specific date ranges, and manage employee reservation requests through a role-based approval workflow.

### System Architecture
The application follows a modular Django structure separated into three domain apps:
* **`users`:** Handles user registration, JWT authentication, profile management, and role assignment.
* **`resources`:** Manages equipment categories, inventory quantities, locations, and active/inactive status tracking.
* **`bookings`:** Handles multi-item reservation requests, date-overlap inventory checks, employee cancellations, and manager approval/rejection workflows.

### Technology Stack
* **Runtime & Framework:** Python 3.10, Django, Django REST Framework
* **Authentication:** JSON Web Tokens (`djangorestframework-simplejwt`)
* **Database:** MySQL (`utf8mb4`)

---

## 2. Authentication & Role-Based Access Control (RBAC)

### Authentication Flow
1. Clients submit credentials to `POST /api/users/login/` to obtain an `access` token and a `refresh` token.
2. Protected endpoints require the `access` token in the HTTP header:
   ```http
   Authorization: Bearer <access_token>
   ```
3. Expired `access` tokens can be renewed via `POST /api/users/token/refresh/`.

### Role Permissions Matrix

| Action / Endpoint Group | `employee` | `resource_manager` | `admin` |
| :--- | :---: | :---: | :---: |
| Register account & manage own profile | Allowed | Allowed | Allowed |
| List, update roles, or delete users | Denied | Denied | Allowed |
| Browse active resources & categories | Allowed | Allowed | Allowed |
| View inactive resources | Denied | Allowed | Allowed |
| Create, update, or deactivate resources/categories | Denied | Allowed | Allowed |
| Check resource availability by date range | Allowed | Allowed | Allowed |
| Submit booking & view own booking history | Allowed | Allowed | Allowed |
| Cancel own `pending` or `approved` future booking | Allowed | Allowed | Allowed |
| View all bookings & approve/reject requests | Denied | Allowed | Allowed |

---

## 3. Database Schema & Constraints

The relational schema consists of five core tables in MySQL:

### 3.1 `User` (`users_user`)
Extends Django's `AbstractUser`.
* **`id`** (`BigAutoField`, PK)
* **`username`** (`CharField`, Unique)
* **`email`** (`EmailField`, Unique)
* **`password`** (`CharField`, hashed)
* **`role`** (`CharField`: `'employee'`, `'resource_manager'`, `'admin'`; default `'employee'`)
* **`department`** (`CharField`)
* **`phone_number`** (`CharField`)

### 3.2 `Category` (`resources_category`)
* **`id`** (`BigAutoField`, PK)
* **`name`** (`CharField`, Unique)
* **`description`** (`TextField`, optional)
* **`created_at`** (`DateTimeField`, auto-populated)

### 3.3 `Resource` (`resources_resource`)
* **`id`** (`BigAutoField`, PK)
* **`name`** (`CharField`)
* **`description`** (`TextField`, optional)
* **`category_id`** (`ForeignKey` → `Category`, `ON DELETE PROTECT`)
* **`total_quantity`** (`PositiveIntegerField`)
* **`available_quantity`** (`PositiveIntegerField`)
* **`location`** (`CharField`)
* **`status`** (`CharField`: `'active'`, `'inactive'`; default `'active'`)
* **`managed_by_id`** (`ForeignKey` → `User`, `ON DELETE SET NULL`, nullable)
* **`created_at` / `updated_at`** (`DateTimeField`)
* **Database Constraint:** `CheckConstraint` enforcing `available_quantity <= total_quantity`.

### 3.4 `Booking` (`bookings_booking`)
* **`id`** (`BigAutoField`, PK)
* **`user_id`** (`ForeignKey` → `User`, `ON DELETE CASCADE`)
* **`start_date`** (`DateTimeField`)
* **`end_date`** (`DateTimeField`)
* **`purpose`** (`TextField`, optional)
* **`status`** (`CharField`: `'pending'`, `'approved'`, `'rejected'`, `'cancelled'`, `'completed'`; default `'pending'`)
* **`reviewed_by_id`** (`ForeignKey` → `User`, `ON DELETE SET NULL`, nullable)
* **`rejection_reason`** (`TextField`, optional)
* **`created_at` / `updated_at`** (`DateTimeField`)
* **Database Constraint:** `CheckConstraint` enforcing `end_date > start_date`.

### 3.5 `BookingItem` (`bookings_bookingitem`)
* **`id`** (`BigAutoField`, PK)
* **`booking_id`** (`ForeignKey` → `Booking`, `ON DELETE CASCADE`)
* **`resource_id`** (`ForeignKey` → `Resource`, `ON DELETE PROTECT`)
* **`quantity`** (`PositiveIntegerField`)
* **Database Constraints:**
  * `UniqueConstraint` on `(booking_id, resource_id)` to prevent duplicate items in one booking.
  * `CheckConstraint` enforcing `quantity >= 1`.

---

## 4. API Endpoints Reference

All list endpoints return paginated responses (`PageNumberPagination`, 10 items per page).

### 4.1 Users & Authentication (`/api/users/`)

| Method | Endpoint | Auth / Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/users/register/` | Public | Register a new employee account |
| `POST` | `/api/users/login/` | Public | Obtain JWT `access` and `refresh` tokens |
| `POST` | `/api/users/token/refresh/` | Public | Refresh an expired `access` token |
| `GET` | `/api/users/profile/` | Authenticated | Retrieve current user's profile |
| `PATCH` | `/api/users/profile/` | Authenticated | Update current user's profile (`role` is read-only) |
| `GET` | `/api/users/manage/` | Admin | List all registered users |
| `GET / PATCH / DELETE` | `/api/users/manage/<id>/` | Admin | Retrieve, update role, or delete a specific user |

### 4.2 Equipment & Categories (`/api/resources/`)

| Method | Endpoint | Auth / Role | Query Filters / Notes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/resources/categories/` | Authenticated | List all equipment categories |
| `POST` | `/api/resources/categories/` | Manager / Admin | Create a new category |
| `GET / PATCH / DELETE` | `/api/resources/categories/<id>/` | Manager / Admin | View, update, or delete a category |
| `GET` | `/api/resources/` | Authenticated | Supports `?category=`, `?location=`, `?available=true/false`, `?status=`, `?search=` |
| `POST` | `/api/resources/` | Manager / Admin | Add a new resource to inventory |
| `GET` | `/api/resources/<id>/` | Authenticated | View resource details |
| `PATCH / DELETE` | `/api/resources/<id>/` | Manager / Admin | Update quantities, deactivate (`status: "inactive"`), or delete |

### 4.3 Bookings & Availability (`/api/bookings/`)

| Method | Endpoint | Auth / Role | Query Filters / Notes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/bookings/` | Authenticated | Employees see own bookings; Managers/Admins see all. Supports `?status=`, `?user=`, `?resource=`, `?start_date=`, `?end_date=` |
| `POST` | `/api/bookings/` | Authenticated | Submit a new booking request (`status` defaults to `pending`) |
| `GET` | `/api/bookings/<id>/` | Authenticated | View booking details and line items |
| `POST` | `/api/bookings/<id>/cancel/` | Owner / Admin | Cancel a `pending` or `approved` booking prior to `start_date` |
| `POST` | `/api/bookings/<id>/approve/` | Manager / Admin | Approve a `pending` booking after re-validating stock |
| `POST` | `/api/bookings/<id>/reject/` | Manager / Admin | Reject a `pending` booking (requires `rejection_reason`) |
| `GET` | `/api/bookings/availability/` | Authenticated | Requires `?start_date=<ISO>&end_date=<ISO>`; returns available quantities per active resource |

---

## 5. Sample Request & Response Payloads

### Create Booking (`POST /api/bookings/`)
**Request:**
```json
{
  "start_date": "2026-11-20T09:00:00Z",
  "end_date": "2026-11-22T17:00:00Z",
  "purpose": "Client presentation",
  "items": [
    {
      "resource": 1,
      "quantity": 2
    }
  ]
}
```

**Response (`201 Created`):**
```json
{
  "id": 1,
  "user": 3,
  "user_username": "alice_dev",
  "start_date": "2026-11-20T09:00:00Z",
  "end_date": "2026-11-22T17:00:00Z",
  "purpose": "Client presentation",
  "status": "pending",
  "reviewed_by": null,
  "reviewed_by_username": null,
  "rejection_reason": "",
  "items": [
    {
      "id": 1,
      "resource": 1,
      "resource_name": "Epson EB-X49 Projector",
      "quantity": 2
    }
  ],
  "created_at": "2026-11-13T11:30:00Z",
  "updated_at": "2026-11-13T11:30:00Z"
}
```

### Reject Booking (`POST /api/bookings/1/reject/`)
**Request:**
```json
{
  "rejection_reason": "Projectors reserved for annual board meeting."
}
```

---

## 6. Core Business Rules & Error Handling

### Date-Overlap Availability Calculation
* Two time intervals $[S_1, E_1]$ and $[S_2, E_2]$ overlap when:
  $$S_1 < E_2 \quad \text{and} \quad E_1 > S_2$$
* Only bookings with `status = 'approved'` reserve inventory. `pending`, `rejected`, and `cancelled` bookings do not block stock.
* Remaining capacity for a requested window is computed as:
  $$\text{Available} = \text{Resource.total\_quantity} - \sum (\text{Overlapping Approved Quantities})$$
* Availability is checked both when an employee submits a booking and atomically (`select_for_update`) when a manager approves a booking, preventing race conditions when multiple pending requests compete for the same equipment.

### Standard HTTP Status Codes
* **`200 OK`:** Request succeeded (`GET`, `PATCH`, `approve`, `reject`, `cancel`).
* **`201 Created`:** Resource, category, user, or booking created (`POST`).
* **`400 Bad Request`:** Validation error (invalid date range, insufficient stock for dates, inactive resource, or missing rejection reason).
* **`401 Unauthorized`:** Missing, malformed, or expired JWT `access` token.
* **`403 Forbidden`:** Authenticated user lacks the required role or ownership for the action.
* **`404 Not Found`:** Requested record ID does not exist.
