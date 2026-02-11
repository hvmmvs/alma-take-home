# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI App                              │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Public   │    │  Protected   │    │     Dependencies      │  │
│  │ Endpoints │    │  Endpoints   │    │                       │  │
│  │          │    │              │    │  get_db()              │  │
│  │ POST     │    │ GET /leads   │    │  get_current_user()   │  │
│  │ /leads   │    │ GET /leads/id│    │  get_email_service()  │  │
│  │          │    │ PATCH /leads │    │                       │  │
│  │ POST     │    │              │    └───────────────────────┘  │
│  │ /auth    │    │  (JWT req.)  │                               │
│  │ /login   │    │              │                               │
│  └────┬─────┘    └──────┬───────┘                               │
│       │                 │                                        │
│       └────────┬────────┘                                        │
│                ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Service Layer                          │   │
│  │                                                           │   │
│  │  lead_service.py     file_service.py    email_service.py  │   │
│  │  - create_lead()     - save_resume()    - EmailService    │   │
│  │  - list_leads()                         - LoggingEmail    │   │
│  │  - get_lead()                             Service (stub)  │   │
│  │  - update_lead_state()                                    │   │
│  └─────────┬────────────────────────────────┬────────────────┘   │
│            │                                │                    │
│            ▼                                ▼                    │
│  ┌──────────────────┐             ┌──────────────────┐          │
│  │   SQLAlchemy      │             │   Local FS       │          │
│  │   Async Session   │             │   (uploads/)     │          │
│  │        │          │             └──────────────────┘          │
│  │        ▼          │                                           │
│  │   SQLite (async)  │                                           │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Request Lifecycle

### 1. Public Lead Submission (`POST /api/leads`)

```
Client (multipart form)
  │
  ▼
Endpoint: parse Form fields + UploadFile
  │
  ▼
file_service.save_resume()
  ├── Validate extension (.pdf, .doc, .docx)
  ├── Validate size (< 10MB)
  └── Write to uploads/{uuid}.{ext}
  │
  ▼
lead_service.create_lead()
  ├── Insert Lead row (state=PENDING)
  ├── Email prospect: "Thank you for your submission"
  └── Email attorney: "New lead submitted"
  │
  ▼
get_db() commits transaction
  │
  ▼
201 Created + LeadCreateResponse (JSON)
```

### 2. Authentication (`POST /api/auth/login`)

```
Client (JSON: username + password)
  │
  ▼
Endpoint: compare username to env var
  │
  ▼
security.verify_password(input, stored_bcrypt_hash)
  │
  ▼
security.create_access_token(username)
  │
  ▼
200 OK + { access_token, token_type: "bearer" }
```

### 3. Protected Lead Management (`GET /api/leads`, `PATCH /api/leads/{id}`)

```
Client (Authorization: Bearer <token>)
  │
  ▼
get_current_user() dependency
  ├── Extract token from Authorization header
  ├── Decode JWT, verify signature + expiry
  └── Confirm username matches internal user
  │
  ▼
Endpoint → Service Layer → Database
  │
  ▼
200 OK + JSON response
```

### 4. State Transition (`PATCH /api/leads/{id}`)

```
PENDING ──────► REACHED_OUT
  (only valid transition, no other transitions allowed)
```

## Project Structure

```
alma/
├── app/
│   ├── main.py                 # App entry point, lifespan events
│   ├── core/
│   │   ├── config.py           # Settings (env vars, .env file)
│   │   ├── database.py         # Async engine, session, get_db
│   │   └── security.py         # JWT encode/decode, bcrypt
│   ├── models/
│   │   ├── base.py             # SQLAlchemy DeclarativeBase
│   │   └── lead.py             # Lead model + LeadState enum
│   ├── schemas/
│   │   ├── auth.py             # LoginRequest, LoginResponse
│   │   └── lead.py             # Lead response/request schemas
│   ├── api/
│   │   ├── router.py           # Mounts all sub-routers under /api
│   │   ├── dependencies.py     # get_current_user (JWT validation)
│   │   └── endpoints/
│   │       ├── auth.py         # POST /api/auth/login
│   │       └── leads.py        # All lead endpoints
│   └── services/
│       ├── lead_service.py     # Lead CRUD + email dispatch
│       ├── file_service.py     # Resume upload + validation
│       └── email_service.py    # ABC + logging stub
├── scripts/
│   ├── setup_env.py            # Interactive .env generator
│   ├── login.py                # CLI login → saves .token
│   ├── submit_lead.py          # CLI lead submission
│   ├── list_leads.py           # CLI lead listing
│   └── reach_out.py            # CLI state transition
├── tests/
│   ├── conftest.py             # Fixtures: in-memory DB, test client
│   ├── test_auth.py            # Auth endpoint tests
│   ├── test_leads_public.py    # Public submission tests
│   ├── test_leads_internal.py  # Protected endpoint tests
│   └── test_email_service.py   # Email service tests
└── uploads/                    # Resume file storage
```

## Data Model

### Lead

| Column       | Type                       | Notes                              |
|-------------|----------------------------|-------------------------------------|
| `id`        | `String` (UUID v4)          | Primary key, app-generated          |
| `first_name`| `String`                    | Required                            |
| `last_name` | `String`                    | Required                            |
| `email`     | `String`                    | Required, indexed                   |
| `resume_path`| `String`                    | Relative path to uploaded file (required) |
| `state`     | `Enum(PENDING, REACHED_OUT)`| Default: `PENDING`                  |
| `created_at`| `DateTime`                  | Server-generated                    |
| `updated_at`| `DateTime`                  | Auto-updated on change              |

No users table exists. The single internal user's credentials are stored in environment variables.

## Email Notifications

When a lead is submitted, emails are sent to both the prospect and an attorney:

| Recipient  | Subject                           |
|------------|-----------------------------------|
| Prospect   | "Thank you for your submission"   |
| Attorney   | "New lead submitted"              |

In this implementation, all emails are printed to stdout (via `LoggingEmailService`) rather than sent. The `EmailService` abstract base class defines the interface; swapping to a real provider requires implementing a single method (`send_email`) and updating the `get_email_service()` factory.

## Testing Strategy

Tests use an **in-memory SQLite database** and override the `get_db` dependency so no persistent state is needed. The test client (`httpx.AsyncClient` with `ASGITransport`) makes real HTTP requests against the app without starting a server.

Coverage includes:
- **Auth:** successful login, wrong password, wrong username
- **Public leads:** submission with resume, missing resume rejected, invalid email, disallowed file types
- **Protected leads:** unauthorized access, listing, retrieval, state transition, invalid transition
- **Email service:** logging output, factory function

```bash
pytest          # run all 15 tests
pytest -v       # verbose output
```
