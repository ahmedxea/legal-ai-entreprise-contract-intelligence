# API Reference

Interactive documentation is available at `http://localhost:8000/docs` (development) or the deployed backend URL `/docs`.

## Authentication

All contract endpoints require a valid session cookie. Obtain one via the login endpoint. The cookie is set as `HttpOnly` and sent automatically by the browser on subsequent requests.

### POST /api/auth/register

Register a new user account.

```json
{ "email": "user@example.com", "password": "...", "full_name": "...", "organization": "..." }
```

### POST /api/auth/login

Authenticate and receive a session cookie.

```json
{ "email": "user@example.com", "password": "..." }
```

### GET /api/auth/me

Returns the authenticated user's profile.

### POST /api/auth/logout

Clears the session cookie.

---

## Contracts

### GET /api/contracts/

List contracts for the authenticated user.

Query parameters: `limit` (default 20, max 100), `offset` (default 0).

### POST /api/contracts/upload

Upload a contract file. Accepts `multipart/form-data`.

Query parameters: `language` (`en` or `ar`), `industry` (optional).

Returns the contract record. Text extraction starts automatically in the background.

### GET /api/contracts/{id}

Get a single contract with its current status.

Status values: `uploaded`, `extracting`, `extracted`, `processing`, `analyzed`, `failed`.

### POST /api/contracts/{id}/analyze

Trigger Phase 2 AI analysis. Returns immediately; poll the contract status to detect completion.

### GET /api/contracts/{id}/analysis

Returns the full analysis result: entities, summary, risks, missing clauses, and overall risk score.

### GET /api/contracts/{id}/text

Returns the raw extracted text and paragraph list.

### DELETE /api/contracts/{id}

Permanently deletes the contract and all associated analysis data.

---

## Clause Generator

### POST /api/clauses/generate-for-risk

Generate a contract-ready clause for a specific risk or missing clause.

```json
{
  "clause_type": "liability",
  "risk_description": "No limitation of liability found",
  "jurisdiction": "uk",
  "contract_context": "SaaS agreement"
}
```

Returns the generated clause text, explanation, CUAD category, and whether a template was used.

### GET /api/clauses/cuad-templates

Returns all available CUAD clause templates with their placeholders.

---

## Dashboard

### GET /api/contracts/dashboard

Returns aggregate statistics: total contracts, analyzed count, pending count, high-risk count, average risk score, and average compliance score.

---

## Health

### GET /health

Returns backend health status including Ollama connectivity.

```json
{ "status": "healthy", "environment": "production", "ollama": "connected" }
```
