# Design Document

## Problem Statement

Alma needs an internal tool to manage prospective client leads for immigration law services. Prospects submit their information (name, email, resume) through a public-facing form. Attorneys then review incoming leads and mark them as contacted. The system must notify both parties via email at key moments: when a lead is submitted and when an attorney reaches out.

## Design Decisions

### 1. FastAPI with Async SQLAlchemy

**Choice:** FastAPI as the web framework, SQLAlchemy 2.0 with async support, SQLite via aiosqlite.

**Why:**
- FastAPI provides automatic OpenAPI docs (Swagger UI), request validation via Pydantic, and dependency injection out of the box. This means less boilerplate and a self-documenting API that reviewers can interact with immediately at `/docs`.
- Async SQLAlchemy keeps the entire stack non-blocking. Even though SQLite is a single-writer database, the async driver (`aiosqlite`) ensures the event loop is never blocked during I/O — this is important if the app were to later switch to PostgreSQL without rewriting the data layer.
- SQLite was chosen for simplicity (zero infrastructure, single file). The async engine abstraction means swapping to PostgreSQL is a one-line config change (`DATABASE_URL`).

**Tradeoff:** SQLite has write concurrency limitations. For a toy/interview project this is fine; in production you'd point `DATABASE_URL` at PostgreSQL.

### 2. Single Hardcoded Internal User (No Users Table)

**Choice:** One internal user with credentials stored in environment variables. No `users` table.

**Why:**
- The spec calls for a single internal attorney view. Building a full user management system (registration, roles, password reset) would be over-engineering for the stated requirements.
- Environment variables are the standard way to handle secrets in twelve-factor apps. The `setup_env.py` script makes onboarding frictionless — run it once and the `.env` file is ready.
- The bcrypt hash is stored (never the plaintext), and the JWT secret is randomly generated per environment.

**Tradeoff:** Adding a second internal user means either duplicating env vars or building a users table. This was a deliberate scope decision — the architecture (JWT + dependency injection) makes it straightforward to add a users table later without changing the endpoint signatures.

### 3. UUID String Primary Keys

**Choice:** Primary keys are UUID v4 strings, not auto-incrementing integers.

**Why:**
- **No information leakage.** Sequential IDs reveal how many leads exist and allow enumeration (`/api/leads/1`, `/api/leads/2`, ...). UUIDs are opaque.
- **Portability.** UUIDs are generated in the application layer, not the database. This avoids SQLite-specific auto-increment behavior and makes the data model portable across databases.
- Stored as strings (not native UUID columns) for SQLite compatibility. If migrating to PostgreSQL, these can be swapped to native `UUID` columns without changing application code.

### 4. Service Layer Pattern

**Choice:** Business logic lives in `app/services/`, not in the endpoint functions. Endpoints are thin HTTP adapters.

**Why:**
- **Separation of concerns.** The endpoint layer handles HTTP specifics (status codes, form parsing, dependency injection). The service layer handles domain logic (create lead, dispatch emails on submission, validate state transitions). This makes each layer independently testable.
- **Reusability.** The same `create_lead()` function could be called from a CLI tool, a background job, or a different API version without duplicating logic.
- Services receive their dependencies (DB session, email service) as parameters rather than importing globals. This makes them easy to test with mocks and stubs.

### 5. Email Service — Strategy Pattern with Logging Stub

**Choice:** Abstract `EmailService` base class with a `LoggingEmailService` implementation that prints to stdout instead of sending real emails.

**Why:**
- The spec requires that emails be sent to both the prospect and an attorney when a lead is submitted. The Strategy pattern (ABC + concrete implementation) makes this explicit: the interface is defined, the integration point is wired into `create_lead()`, and swapping to a real email provider (SendGrid, SES) means writing a new class that implements `send_email()` and changing one line in `get_email_service()`.
- Using FastAPI's dependency injection (`Depends(get_email_service)`) means the swap can happen without touching any endpoint or service code.
- `print()` was chosen over `logging.info()` for the stub output so that it's immediately visible in the terminal during testing, making it obvious to reviewers that the email hook fired.

### 6. Lead State Machine with Explicit Transition Validation

**Choice:** `LeadState` is a Python enum (`PENDING`, `REACHED_OUT`). The only valid transition is `PENDING → REACHED_OUT`, enforced in the service layer.

**Why:**
- The spec describes a one-way workflow: leads arrive as `PENDING` and are marked `REACHED_OUT` by an attorney. Encoding this as an explicit guard (`if lead.state != PENDING or new_state != REACHED_OUT: raise`) prevents invalid states and makes the business rule visible in the code.
- If additional states are needed later (e.g., `CLOSED`, `CONVERTED`), the enum and validation logic are in one place (`lead_service.py:update_lead_state`).

**Tradeoff:** A more complex state machine (with a transition table) would be warranted if there were many states. For two states, an `if` statement is clearer than a framework.

### 7. File Upload Security

**Choice:** Uploaded resumes are renamed to `{uuid}.{ext}` and stored in a local `uploads/` directory. Only `.pdf`, `.doc`, and `.docx` extensions are allowed. Files are capped at 10 MB.

**Why:**
- **Path traversal prevention.** User-supplied filenames are never used for storage. A file named `../../etc/passwd.pdf` becomes `a1b2c3d4.pdf`.
- **Extension allowlisting** prevents upload of executable files. Only document formats are accepted.
- **Size limiting** prevents denial-of-service via large uploads. The file is read into memory once and checked before writing.
- The database stores only the relative path, making the storage backend swappable (local → S3) by changing `file_service.py`.

### 8. JWT Authentication with HTTPBearer

**Choice:** `POST /api/auth/login` returns a JWT. Protected endpoints use FastAPI's `HTTPBearer` security scheme.

**Why:**
- `HTTPBearer` gives us the lock icon in Swagger UI for free — reviewers can authenticate directly in the browser and test protected endpoints without curl.
- JWTs are stateless: no server-side session storage needed. The token contains the username and expiry, verified on each request via `get_current_user`.
- The token expiry (default 60 minutes) is configurable via environment variable.

### 9. Transaction Management in the Dependency Layer

**Choice:** The `get_db` dependency yields a session, commits on success, and rolls back on exception.

**Why:**
- Endpoints and services don't need to call `commit()` or `rollback()` — the dependency handles it. This eliminates an entire class of bugs (forgotten commits, leaked transactions).
- Services use `flush()` to push changes to the database (getting generated defaults like `created_at`) and `refresh()` to load them back, all within the same transaction. The commit happens only after the endpoint returns successfully.

### 10. Project Configuration via `pydantic-settings`

**Choice:** All configuration is managed through a single `Settings` class that reads from environment variables and `.env` files.

**Why:**
- Type-safe configuration with validation. If `JWT_EXPIRE_MINUTES` is set to `"not_a_number"`, pydantic raises an error at startup — not at runtime when the value is first used.
- The `.env` file path is resolved relative to the project root (via `Path(__file__)`), not the current working directory. This prevents a class of bugs where running the server from a subdirectory silently falls back to default values.
- The `setup_env.py` script generates the `.env` interactively, including a random JWT secret and bcrypt-hashed password, so there are no secrets in source control.
