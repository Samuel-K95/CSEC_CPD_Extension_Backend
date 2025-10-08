
# CSEC CPD Extension Backend

This is the backend for the CSEC CPD Extension, a web application for managing and tracking programming contest participation, attendance, and Codeforces-style rating updates for the CSEC community.

**Features:**
- User registration and authentication (JWT, refresh tokens)
- Role-based access (Admin, Participant, Preparer)
- Contest creation, preparer assignment, and attendance tracking
- Codeforces-style rating calculation and rollback/replay
- RESTful API with FastAPI
- SQLite database (default, can be swapped for PostgreSQL)


## Prerequisites

- Python 3.10 or later
- pip


## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Samuel-K95/CSEC_CPD_Extension_Backend.git
   cd CSEC_CPD_Extension_Backend/backend
   ```

2. **Create and activate a virtual environment:**
   - On Windows:
     ```bash
     python -m venv myvenv
     myvenv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv myvenv
     source myvenv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```


## Running the Application

To start the backend server:

```bash
uvicorn app.main:app --reload
```

The API will be available at: http://127.0.0.1:8000

Interactive API docs: http://127.0.0.1:8000/docs


## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app entrypoint
│   ├── db.py                  # Database setup
│   ├── models.py              # SQLAlchemy models
│   ├── crud/                  # CRUD logic (modularized)
│   ├── routers/               # API route modules (auth, users, contests, attendance, ratings)
│   ├── schemas/               # Pydantic schemas for validation/serialization
│   ├── services/              # Business logic (e.g., Codeforces rating)
│   └── security.py            # Auth utilities (JWT, password hashing)
├── dev.db                     # SQLite database (for development)
├── requirements.txt           # Python dependencies
├── myvenv/                    # Virtual environment (not committed)
└── README.md
```

## Authentication & Testing the API

### 1. Register a User

```http
POST /api/auth/register
Content-Type: application/json

{
   "name": "Alice",
   "email": "alice@example.com",
   "codeforces_handle": "alice_cf",
   "division": "Div 1",
   "password": "yourpassword"
}
```

### 2. Login

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=alice_cf&password=yourpassword
```
Response:
```json
{
   "access_token": "...",
   "refresh_token": "...",
   ...
}
```

### 3. Use Access Token

Add the following header to all protected requests:

```
Authorization: Bearer <access_token>
```

### 4. Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
   "refresh_token": "..."
}
```

### 5. Example: Get Current User Profile

```http
GET /api/users/profile
Authorization: Bearer <access_token>
```

## Running Tests

You can run backend tests (if available) with:

```bash
pytest
```

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes and add tests if needed.
3. Submit a pull request with a clear description.

## License

MIT License. See [LICENSE](../LICENSE) for details.
