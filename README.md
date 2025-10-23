# Backend Transaction Ledger System

A production-style **double-entry accounting and money-transfer backend** built with Node.js, Express, and MongoDB. The service models real banking primitives — users, accounts, an **immutable ledger**, and **idempotent, atomic transactions** — so that every balance in the system is always derivable from an auditable trail of credit and debit entries.

![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)
![Express](https://img.shields.io/badge/Express-5.x-000000?logo=express&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Mongoose-47A248?logo=mongodb&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-orange?logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-ISC-blue)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [The Transfer Flow](#the-transfer-flow)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Security Notes](#security-notes)
- [Roadmap](#roadmap)

---

## Overview

Most toy "wallet" projects store a single `balance` field and mutate it on every transfer. That approach loses history, is impossible to audit, and corrupts easily under concurrency. This project takes the **ledger-first** approach used by real financial systems:

- An account **never** stores a balance directly.
- Every movement of money is recorded as two **immutable** ledger entries — one `DEBIT` and one `CREDIT`.
- A balance is **computed on demand** by aggregating the account's ledger entries.

The result is a system where money is conserved, history is tamper-evident, and every figure can be reconstructed and audited at any time.

## Key Features

- 🔐 **JWT Authentication** — register, login, and logout with HTTP-only cookie + bearer-token support.
- 🚫 **Token Blacklisting** — logged-out tokens are invalidated and auto-expire via a MongoDB TTL index.
- 🏦 **Account Management** — users can open multiple accounts, each with status (`ACTIVE` / `FROZEN` / `CLOSED`) and currency.
- 📒 **Immutable Double-Entry Ledger** — ledger entries cannot be updated or deleted; integrity is enforced at the schema level.
- 💸 **Atomic Transfers** — transfers run inside a **MongoDB multi-document transaction**, so debit and credit always commit together or not at all.
- 🔁 **Idempotency** — every transfer carries an `idempotencyKey`, making retries safe and preventing duplicate charges.
- 📊 **Derived Balances** — account balances are aggregated from the ledger, never stored, eliminating drift.
- 🏛️ **System / Treasury Account** — a privileged system user can inject initial funds into the economy.
- 📧 **Email Notifications** — transactional emails on registration and successful transfers via Nodemailer (Gmail OAuth2).

## Architecture

```
        ┌──────────┐      ┌──────────────┐      ┌──────────────┐
HTTP ─► │  Routes  │ ───► │ Controllers  │ ───► │    Models     │
        └──────────┘      └──────────────┘      └──────────────┘
              │                  │                      │
              ▼                  ▼                      ▼
        Auth Middleware    Email Service          MongoDB (Mongoose)
       (JWT + blacklist)   (Nodemailer)         Users · Accounts ·
                                                Ledger · Transactions
```

The codebase follows a clean, layered separation:

- **Routes** declare endpoints and attach middleware.
- **Middleware** authenticates requests and guards privileged system operations.
- **Controllers** hold business logic and orchestrate the transfer flow.
- **Models** define schemas, validation, and invariants (e.g. ledger immutability, balance aggregation).
- **Services** handle side effects such as outbound email.

## Tech Stack

| Layer            | Technology                                   |
| ---------------- | -------------------------------------------- |
| Runtime          | Node.js                                      |
| Web framework    | Express 5                                    |
| Database         | MongoDB via Mongoose (multi-doc transactions)|
| Authentication   | JSON Web Tokens (`jsonwebtoken`)             |
| Password hashing | `bcryptjs`                                   |
| Cookies          | `cookie-parser`                              |
| Email            | `nodemailer` (Gmail OAuth2)                  |
| Config           | `dotenv`                                     |

## Project Structure

```
.
├── server.js                       # Entry point — loads env, connects DB, starts server
└── src
    ├── app.js                      # Express app, middleware & route wiring
    ├── config
    │   └── db.js                   # MongoDB connection
    ├── middleware
    │   └── auth.middleware.js      # JWT auth + system-user guard
    ├── models
    │   ├── user.model.js           # User + bcrypt password hashing
    │   ├── account.model.js        # Account + ledger-derived balance method
    │   ├── ledger.model.js         # Immutable double-entry ledger
    │   ├── transaction.model.js    # Transfer record + idempotency key
    │   └── blackList.model.js      # Invalidated tokens (TTL index)
    ├── controllers
    │   ├── auth.controller.js      # Register / login / logout
    │   ├── account.controller.js   # Create / list accounts, get balance
    │   └── transaction.controller.js # Transfer flow + initial funds
    ├── routes
    │   ├── auth.routes.js
    │   ├── account.routes.js
    │   └── transaction.routes.js
    └── services
        └── email.service.js        # Registration & transaction emails
```

## Data Model

| Entity          | Purpose                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------- |
| **User**        | Identity. Email/password (hashed with bcrypt). Optional immutable `systemUser` flag.     |
| **Account**     | Belongs to a user. Has `status` and `currency`. Balance is **computed**, never stored.   |
| **Ledger**      | Immutable `CREDIT`/`DEBIT` entry tied to an account and a transaction. Cannot be mutated.|
| **Transaction** | A transfer between two accounts. Tracks `status` and a unique `idempotencyKey`.          |
| **TokenBlacklist** | Revoked JWTs, auto-purged after 3 days via a TTL index.                                |

**Account balance** is derived with a MongoDB aggregation:

```
balance = Σ(CREDIT amounts) − Σ(DEBIT amounts)
```

**Ledger immutability** is enforced by blocking every update/delete hook
(`updateOne`, `deleteOne`, `findOneAndUpdate`, `findOneAndDelete`, …) at the schema level.

## The Transfer Flow

A standard transfer (`POST /api/transactions`) executes a deliberate 10-step pipeline:

1. **Validate request** — `fromAccount`, `toAccount`, `amount`, `idempotencyKey` are required.
2. **Check idempotency** — if the key was already used, return the prior result instead of re-charging.
3. **Check account status** — both accounts must be `ACTIVE`.
4. **Derive sender balance** from the ledger and reject if funds are insufficient.
5. **Open a MongoDB session/transaction** and create the transaction as `PENDING`.
6. **Write the DEBIT** ledger entry for the sender.
7. **Write the CREDIT** ledger entry for the receiver.
8. **Mark the transaction `COMPLETED`.**
9. **Commit** the session atomically (debit + credit + status update succeed or fail together).
10. **Send an email notification** to the sender.

If anything fails before commit, the transaction is rolled back and no partial ledger state remains.

## API Reference

Base URL: `http://localhost:3000`

### Auth — `/api/auth`

| Method | Endpoint    | Auth | Description                          |
| ------ | ----------- | ---- | ------------------------------------ |
| POST   | `/register` | —    | Create a user, returns a JWT cookie. |
| POST   | `/login`    | —    | Authenticate, returns a JWT cookie.  |
| POST   | `/logout`   | —    | Blacklist the current token.         |

### Accounts — `/api/accounts`

| Method | Endpoint              | Auth | Description                        |
| ------ | --------------------- | ---- | --------------------------------- |
| POST   | `/`                   | JWT  | Open a new account.               |
| GET    | `/`                   | JWT  | List the current user's accounts. |
| GET    | `/balance/:accountId` | JWT  | Get an account's derived balance. |

### Transactions — `/api/transactions`

| Method | Endpoint                  | Auth        | Description                                  |
| ------ | ------------------------- | ----------- | -------------------------------------------- |
| POST   | `/`                       | JWT         | Transfer funds between two accounts.         |
| POST   | `/system/initial-funds`   | System User | Inject initial funds from the system account.|

**Example — create a transfer**

```bash
curl -X POST http://localhost:3000/api/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "fromAccount": "<accountId>",
    "toAccount": "<accountId>",
    "amount": 500,
    "idempotencyKey": "a1b2c3-unique-key"
  }'
```

## Getting Started

### Prerequisites

- Node.js 18+
- A MongoDB instance that supports transactions (a **replica set** — e.g. MongoDB Atlas or a local replica set)

### Installation

```bash
# 1. Clone
git clone https://github.com/suleman-the-stammer/backend-transaction-ledger-system.git
cd backend-transaction-ledger-system

# 2. Install dependencies
npm install

# 3. Configure environment (see below)
cp .env.example .env   # then edit values

# 4. Run
npm run dev    # development (nodemon)
npm start      # production
```

The server starts on **port 3000**: `Ledger Service is up and running`.

> **Note:** MongoDB multi-document transactions require a replica set. A standalone `mongod` will reject the transfer flow.

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>

# Auth
JWT_SECRET=your_super_secret_key

# Email (Gmail OAuth2)
EMAIL_USER=you@gmail.com
CLIENT_ID=your_google_oauth_client_id
CLIENT_SECRET=your_google_oauth_client_secret
REFRESH_TOKEN=your_google_oauth_refresh_token
```

## Security Notes

- Passwords are hashed with **bcrypt** and never selected by default (`select: false`).
- JWTs expire after 3 days and can be **revoked** via the blacklist on logout.
- Ledger entries are **immutable** — the audit trail cannot be silently rewritten.
- Privileged "initial funds" operations are gated behind a dedicated **system-user** middleware.

## Roadmap

- [ ] Reversal / refund flow for `REVERSED` transactions
- [ ] Pagination & filtering for transaction history
- [ ] Rate limiting and request validation middleware
- [ ] Automated test suite (unit + integration)
- [ ] OpenAPI / Swagger documentation
- [ ] Containerized deployment (Docker + replica set)

---

> Built as a study in correct, auditable financial backend design — where **balances are derived, money is conserved, and history is immutable.**
