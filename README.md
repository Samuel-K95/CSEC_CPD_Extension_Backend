# CSEC CPD Extension Backend

This is the backend for the CSEC CPD Extension, a web application for tracking Continuing Professional Development.

## Prerequisites

- Python 3.10 or later
- pip

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Samuel-K95/CSEC_CPD_Extension_Backend.git
   cd CSEC_CPD_Extension_Backend
   ```

2. **Create and activate a virtual environment:**

   - On Windows:
     ```bash
     python -m venv myvenv
     myvenv\\Scripts\\activate
     ```

   - On macOS and Linux:
     ```bash
     python3 -m venv myvenv
     source myvenv/bin/activate
     ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To run the backend server, use the following command:

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## Project Structure

```
backend/
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── crud.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   └── services/
├── dev.db
├── myvenv/
└── requirements.txt
```
