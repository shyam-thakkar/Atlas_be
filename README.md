# Atlas Backend

This is the Django REST Framework backend for the **Atlas** application. It handles user authentication (Email/Password & Google OAuth), user profiles, and resume management.

## 🚀 Features

- **Authentication**: 
  - JWT Authentication (Access & Refresh tokens).
  - Secure Email/Password Signup & Login.
  - Google OAuth Integration.
  - Token Refresh Rotation for security.
- **User Profiles**: Manage user details and metadata.
- **Resume System**: Upload, parse, and extracting data from resumes.
- **Modern Stack**: Django 5+, Django REST Framework, PostgreSQL.

## 🛠️ Tech Stack

- **Framework**: Django & Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Authentication**: `rest_framework_simplejwt`
- **CORS**: `django-cors-headers`

## ⚙️ Setup & Installation

### 1. Prerequisite
Ensure you have Python 3.10+ and PostgreSQL installed.

### 2. Clone the Repository
```bash
git clone <repository_url>
cd atlas_backend
```

### 3. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Environment Variables
Create a `.env` file in the root directory (`atlas_backend/.env`) and add the following:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DB_NAME=atlas_db
DB_USER=atlas_user
DB_PASSWORD=Atlas@123
DB_HOST=localhost
DB_PORT=5432

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Authentication (SimpleJWT)
# Note: Tokens are stored in the client (localStorage).
ACCESS_TOKEN_LIFETIME=5  # Minutes (example)
REFRESH_TOKEN_LIFETIME=1 # Days
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/`.

---

## 🔑 Authentication Flow

All authentication endpoints return JWT `access` and `refresh` tokens in the response body. The frontend is responsible for storing these tokens (e.g., in `localStorage`) and attaching the `access` token to the `Authorization` header of subsequent requests.

**Header Format:**
```
Authorization: Bearer <access_token>
```

### Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/signup/` | Register a new user with Name, Email, Password. | ❌ |
| `POST` | `/api/auth/login/` | Login with Email & Password. Returns tokens. | ❌ |
| `POST` | `/api/auth/google/` | Login with Google ID Token. Returns tokens. | ❌ |
| `POST` | `/api/auth/token/refresh/`| Get a new Access Token using a Refresh Token. | ❌ |
| `POST` | `/api/auth/logout/` | Logout (Blacklist Refresh Token). | ❌ |
| `GET` | `/api/auth/me/` | Get current user details. | ✅ |

#### Sample Login Response
```json
{
    "message": "Login successful",
    "user": {
        "email": "user@example.com",
        "name": "John Doe"
    },
    "tokens": {
        "access": "eyJhbGciOiJIUz...",
        "refresh": "eyJhbGciOiJIUz..."
    }
}
```

---

## 👤 Profiles API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/profiles/me/` | Get current user's profile. |
| `PUT` | `/api/profiles/me/` | Update profile details. |

---

## 📄 Resumes API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/resumes/upload/` | Upload a resume (PDF/DOCX). |
| `GET` | `/api/resumes/list/` | List user resumes. |
