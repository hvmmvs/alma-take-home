# Alma Lead Management API

A FastAPI application for managing immigration law leads. Prospects submit their information through a public form, and internal staff can view and manage leads through authenticated endpoints.

## Quick Start

### 1. Install dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set up your `.env` file

Run the interactive setup script — it will prompt you for an admin username and password, then generate the `.env` file with a hashed password and a random JWT secret:

```bash
python scripts/setup_env.py
```

You'll see something like:

```
=== Alma .env Setup ===

Internal username [admin]: admin
Internal password:
Confirm password:

.env written to /path/to/alma/.env
  Username: admin
  Password: (hidden)
```

### 3. Start the server

```bash
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the Swagger UI.

---

## CLI Scripts

All scripts live in the `scripts/` directory and use only the Python standard library (no extra dependencies needed beyond the project install). The server must be running for these to work.

### Submit a lead (public — no login needed)

```bash
python scripts/submit_lead.py
```

You'll be prompted for first name, last name, email, and a resume file path (`.pdf`, `.doc`, `.docx`):

```
=== Submit a New Lead ===

First name: Jane
Last name: Doe
Email: jane@example.com
Resume file path (.pdf, .doc, .docx): ./resume.pdf

Lead submitted successfully!
  ID:    a1b2c3d4-...
  Name:  Jane Doe
  Email: jane@example.com
  State: PENDING
  Resume: uploads/a1b2c3d4.pdf

sent email to prospect: jane@example.com
sent email to attorney: attorney@example.com
```

On submission, emails are sent to both the prospect and an attorney. (In this implementation, emails are printed to stdout rather than actually sent.)

### Log in (required for internal scripts)

```bash
python scripts/login.py
```

Enter the credentials you chose during setup. The token is saved to `.token` and used automatically by the other scripts:

```
=== Alma Login ===

Username: admin
Password:
Login successful! Token saved.
```

### List all leads

```bash
python scripts/list_leads.py
```

Displays a table of all leads:

```
#    ID                                    Name                      Email                          State
--------------------------------------------------------------------------------------------------------------
1    a1b2c3d4-...                          Jane Doe                  jane@example.com               PENDING
```

### Mark a lead as reached out

```bash
python scripts/reach_out.py
```

Shows all pending leads and lets you select one to mark as `REACHED_OUT`:

```
Pending leads:

  #    Name                      Email
  ------------------------------------------------------------
  1    Jane Doe                  jane@example.com

Select a lead to mark as REACHED_OUT (1-1): 1

Done! Jane Doe marked as REACHED_OUT.
```

---

## API Reference

| Method  | Path                  | Auth   | Description                          |
|---------|-----------------------|--------|--------------------------------------|
| `POST`  | `/api/auth/login`     | Public | Login with username/password → JWT   |
| `POST`  | `/api/leads`          | Public | Submit a lead (multipart form)       |
| `GET`   | `/api/leads`          | JWT    | List all leads                       |
| `GET`   | `/api/leads/{id}`     | JWT    | Get a single lead                    |
| `PATCH` | `/api/leads/{id}`     | JWT    | Update lead state (PENDING → REACHED_OUT) |

## Documentation

- **[DESIGN.md](DESIGN.md)** — Design decisions and rationale for every major architectural choice
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture, request lifecycles, data model, and project structure

## Running Tests

```bash
pytest
```
