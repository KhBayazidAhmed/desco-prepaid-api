# DESCO Prepaid API Reference

Unofficial documentation for the authenticated [DESCO prepaid portal](https://prepaid.desco.org.bd/).

**Base URL:** `https://prepaid.desco.org.bd/api`

The current portal uses username/password login, session cookies, and CSRF protection. Retrieve accounts linked to the signed-in user, then use their internal `accountId` to retrieve balances. An account number or meter number is not the `accountId`.

The previous reference is preserved in [docs/legacy-api.md](docs/legacy-api.md). Those older endpoints have not been reverified; this update does not establish whether they remain available.

## Verification

Inspected on **2026-11-08** using Ego Lite and the deployed frontend bundle `assets/index-CN7ZLy9Z.js`.

- **Tested with an existing authenticated browser session:** account listing, daily balance, and realtime eligibility/last result returned HTTP 200.
- **Tested without cookies:** daily balance returned HTTP 401 with `errorCode: "AUTHENTICATION_REQUIRED"`.
- **Identified in frontend source only:** fresh login and realtime request/polling. These still require end-to-end validation. The Python example has local HTTP tests, but has not been tested with a fresh DESCO login.

These are undocumented portal endpoints and can change. Examples below use synthetic account numbers and balances; no credentials or session cookies are included.

## Authentication flow

1. Create an HTTP client with a cookie jar. Keep that same jar throughout the flow.
2. `GET /auth/csrf` to receive the `XSRF-TOKEN` cookie.
3. URL-decode that cookie's value.
4. `POST /auth/login` with the decoded value in `X-XSRF-TOKEN`, the cookies, and a JSON body:
   ```json
   {"username": "YOUR_DESCO_USERNAME", "password": "YOUR_DESCO_PASSWORD"}
   ```
5. Retain cookies set by the login response. Subsequent requests authenticate using those cookies.
6. `GET /accounts`, choose a linked account, then `GET /accounts/{accountId}/balance`.

The frontend sends `Accept: application/json`, uses `credentials: "include"`, adds `Content-Type: application/json` for JSON bodies, and copies `XSRF-TOKEN` to `X-XSRF-TOKEN` on non-GET requests. This is cookie authentication, not bearer-token or API-key authentication.

`GET /auth/session` is the frontend's session-check endpoint. A protected request returning 401 requires signing in again. Session lifetime has not been measured. Do not repeatedly retry invalid credentials.

First-time users should create their portal account and link their electricity account through the website. The example does not automate registration or account linking.

## Daily balance

### List linked accounts

```http
GET /accounts
```

Response excerpt:

```json
{
  "accounts": [
    {
      "accountId": 123,
      "sourceSystem": "TKDES",
      "accountNo": "12345678",
      "meterNo": "123456789012",
      "status": "ACTIVE",
      "linkStatus": "ACTIVE"
    }
  ]
}
```

Choose `accounts[].accountId`. The current flow does not require trying separate `unified` and `tkdes` URL prefixes.

### Fetch balance

```http
GET /accounts/123/balance
Accept: application/json
Cookie: <authenticated session cookies>
```

Response excerpt (the object is returned directly, without the legacy `code/desc/data` wrapper):

```json
{
  "accountNo": "12345678",
  "meterNo": "123456789012",
  "balance": 500.25,
  "meterType": "TKDES",
  "currency": "BDT",
  "balanceSnapshotAt": "2026-11-08T00:00+06:00",
  "timestampSource": "UPSTREAM",
  "timestampAvailable": true,
  "stale": false,
  "currentMonthConsumedTaka": 100.50,
  "readingTime": "2026-11-08 00:00:00"
}
```

The response also includes `consumerMessages` explaining the balance. This is a **daily snapshot**, not a live meter reading. A recharge may appear in recharge history before the next balance update. Check `stale`, `timestampAvailable`, and `balanceSnapshotAt`; an unavailable balance must not be treated as zero.

With your own authenticated cookie jar:

```sh
curl --fail-with-body -b cookies.txt \
  -H 'Accept: application/json' \
  'https://prepaid.desco.org.bd/api/accounts/123/balance'
```

Replace `123` with an ID returned by your account list. The cookie jar must already contain an authenticated session.

## Python example

Python 3.9+; no third-party dependencies:

```sh
python3 examples/balance.py
```

The script prompts for your username and password, stores cookies only in memory, and prints the daily balance for each linked account. Password input is hidden. Keep credentials and cookies private; do not commit them or put them in URLs. For a deployed integration, keep them on the backend.

Run the local tests:

```sh
python3 -m unittest discover -s tests -v
```

## Realtime balance

### Check eligibility and the last result

```http
GET /accounts/realtime-balance
```

The response has `enabled` and a `meters` array. Meter entries include `accountId`, `meterNo`, `meterType`, `status`, `message`, `lastRealtimeBalance`, `lastRealtimeReceivedAt`, `nextEligibleAt`, `attemptsToday`, and `remainingAttempts`.

An observed response had `status: "DAILY_LIMIT_REACHED"` despite positive `remainingAttempts`. Respect the returned status, message, and eligibility times rather than deciding from the counter alone. No new meter reading was requested during inspection because the linked meter had reached its limit.

### Request a reading (source-inspected, not live-tested)

```http
POST /accounts/{accountId}/realtime-balance
Content-Type: application/json
X-XSRF-TOKEN: <URL-decoded XSRF-TOKEN cookie>
Cookie: <session cookies including XSRF-TOKEN>
```

```json
{"idempotencyKey": "<new UUID for this logical request>"}
```

The frontend generates a UUID with `crypto.randomUUID()`. If the response status is `IN_PROGRESS`, take its `requestId` and poll:

```http
GET /accounts/{accountId}/realtime-balance/{requestId}
```

URL-encode `requestId` as a path component. The frontend polls every **2 seconds**, stops when status changes, and stops waiting after **60 seconds**. Poll the GET status endpoint, not the POST endpoint. On `SUCCESS`, read `balance`, `meterNo`, and `receivedAt`.

Other states handled by the frontend include `OFFLINE`, `TIMEOUT`, `UPSTREAM_FAILURE`, `COOLDOWN_ACTIVE`, `DAILY_LIMIT_REACHED`, and `UNAVAILABLE`. Respect cooldowns and daily restrictions; this example deliberately performs daily-balance GETs only.

## Errors and compatibility

Check HTTP status before interpreting JSON. The verified unauthenticated response was:

```json
{
  "errorCode": "AUTHENTICATION_REQUIRED",
  "message": "Please sign in to continue.",
  "correlationId": "<request correlation identifier>"
}
```

Do not assume errors or successful payloads follow the legacy wrapper. An empty linked-account list requires linking an account in the portal. Other usage, summary, and recharge endpoints require separate response verification before migrating their old documentation.
