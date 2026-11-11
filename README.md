# equipment-booking-api
Techleap fullstack onboarding test /

A backend REST API built with Django and Django REST Framework for organizations to manage equipment inventory, track availability, and handle employee booking requests using role-based approval workflows.

## Tech Stack

* **Language:** Python 3.10
* **Framework:** Django, Django REST Framework (DRF)
* **Authentication:** SimpleJWT (JSON Web Tokens)
* **Database:** MySQL (managed locally via MySQL Workbench)

## System Architecture

The project is organized into three modular Django applications:

### 1. `users` App (Completed)
Handles authentication, user profiles, and Role-Based Access Control (RBAC) via a custom `User` model (`AUTH_USER_MODEL = 'users.User'`) extending `AbstractUser` with a unique `email`, `role`, `department`, and `phone_number`.

* **`admin`:** Full system access, user account management, and role assignment.
* **`resource_manager`:** Manages equipment categories and inventory, and approves or rejects booking requests.
* **`employee`:** Views available equipment and submits booking requests.

### 2. `resources` App (In Progress)
Manages organizational equipment inventory and categorization.
* **`Category`:** `name`, `description`
* **`Resource`:** `name`, `serial_number`, `category`, `description`, `location`, `status` (`available`, `maintenance`, `retired`), `managed_by`, `created_at`

### 3. `bookings` App (Planned)
Handles equipment reservations, scheduling conflict checks, and approval workflows.
* **`Booking`:** `user`, `resource`, `start_time`, `end_time`, `purpose`, `status` (`pending`, `approved`, `rejected`, `returned`, `cancelled`), `approved_by`, `rejection_reason`, `created_at` (includes overlap validation to prevent double-booking).

---

## Prerequisites & System Dependencies

Ensure Python 3.10 and MySQL Server are installed on your machine. On Ubuntu/Debian systems, install the required development headers to build the MySQL database connector:

```bash
sudo apt update
sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config
```

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd <project-directory>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install Django djangorestframework djangorestframework-simplejwt mysqlclient
   ```
   *(Alternatively, run `pip install -r requirements.txt` if a requirements file is present.)*

## Database & Environment Configuration

1. **Create the MySQL Database:**
   Open MySQL Workbench or the MySQL CLI and create the database using the `utf8mb4` character set:
   ```sql
   CREATE DATABASE equipment_booking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Configure `settings.py` (or `.env`):**
   Update the `DATABASES` configuration in your project's `settings.py` file (or load these credentials via environment variables) to connect to your local MySQL instance:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'equipment_booking_db',
           'USER': 'your_mysql_username',
           'PASSWORD': 'your_mysql_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```
   Ensure `SECRET_KEY` and `DEBUG` are configured appropriately for your local environment.

## Running the Application

1. **Apply database migrations:**
   ```bash
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

2. **Create an initial admin superuser:**
   ```bash
   python3 manage.py createsuperuser
   ```

3. **Start the development server:**
   ```bash
   python3 manage.py runserver
   ```

The API will be available at `http://127.0.0`.

---

## API Endpoints Reference

### Authentication & Users (`/api/users/`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/users/register/` | Public | Register a new user account (defaults to `employee` role) |
| `POST` | `/api/users/login/` | Public | Authenticate user and obtain JWT `access` and `refresh` tokens |
| `POST` | `/api/users/token/refresh/` | Public | Obtain a new access token using a valid refresh token |
| `GET` | `/api/users/profile/` | Authenticated | Retrieve the logged-in user's profile details |
| `PATCH` | `/api/users/profile/` | Authenticated | Update the logged-in user's profile details |
| `GET` | `/api/users/manage/` | Admin only | List all registered users |
| `GET` | `/api/users/manage/<id>/` | Admin only | Retrieve details for a specific user |
| `PATCH` | `/api/users/manage/<id>/` | Admin only | Update user details or assign user roles |
| `DELETE` | `/api/users/manage/<id>/` | Admin only | Delete a user account |

---

## Project Roadmap

- [x] **Phase 1 — Authentication & User Management (`users`):** Custom user model, JWT authentication, role-based permissions, profile endpoints, and admin user management.
- [ ] **Phase 2 — Equipment Inventory (`resources`):** Category and resource models, CRUD endpoints, and status tracking (`available`, `maintenance`, `retired`).
- [ ] **Phase 3 — Booking & Approval Workflow (`bookings`):** Booking request endpoints, date/time overlap validation, and `resource_manager` approval/rejection actions.

