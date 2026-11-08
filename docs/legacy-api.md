> Historical reference: this documents the older API. Its endpoints and anonymous access have not been reverified against the current portal. See the [current authenticated flow](../README.md).

# DESCO Prepaid API Reference

## Overview

DESCO (Dhaka Electric Supply Company) exposes a public, unauthenticated API for prepaid electricity meter accounts at:

**Base URL:** `https://prepaid.desco.org.bd/api`

The API allows anyone to query:
- Current balance and basic meter info
- Customer / installation details
- Daily consumption history (units + cost)
- Monthly consumption history
- Recharge / payment history

**Important characteristics:**
- No authentication, tokens, API keys, or login required.
- All requests are simple `GET` requests.
- Works by supplying the account number (from the electricity bill).
- Two parallel backend paths exist (`unified` and `tkdes`). Most accounts respond on only one of them.

## Meter Type Paths

All endpoints are available under two prefixes:

- `/unified/customer/...`
- `/tkdes/customer/...`

**How to choose the correct type:**
1. Call the desired endpoint with `unified`.
2. If `data` is `null` or the account is not found, retry with `tkdes`.

Some third-party tools hardcode one path (often `tkdes`).

## Authentication & Headers

None required.

Minimal working request:
```http
GET https://prepaid.desco.org.bd/api/unified/customer/getBalance?accountNo=123456789
```

Recommended headers (not strictly required):
- `Accept: application/json, text/plain, */*`

## Common Response Format

Every successful response follows this structure:

```json
{
  "code": 200,
  "desc": "OK",
  "data": { ... }   // object, array, or null
}
```

- `code`: Numeric status (200 = success, other values indicate issues)
- `desc`: Human-readable message
- `data`: The actual payload (can be `null` for valid accounts with no data, or when the account doesn't exist on that meter type)

Common non-200 codes observed:
- `16001` → "The Account No. does not exist"

## Endpoints

### 1. Get Balance

**Path:**
```
GET /:type/customer/getBalance?accountNo=...
```

**Query Parameters:**
| Parameter   | Type   | Required | Description                          |
|-------------|--------|----------|--------------------------------------|
| `accountNo` | string | Yes      | DESCO prepaid account number         |
| `meterNo`   | string | No       | Optional meter number (some scripts pass it) |

**Example:**
```bash
curl "https://prepaid.desco.org.bd/api/unified/customer/getBalance?accountNo=123456789"
```

**Response `data` fields (when present):**
- `accountNo`
- `meterNo`
- `balance` (current balance in BDT)
- `currentMonthConsumption`
- `readingTime` (last reading timestamp)

### 2. Get Customer Info

**Path:**
```
GET /:type/customer/getCustomerInfo?accountNo=...
```

**Query Parameters:**
- `accountNo` (required)

**Typical `data` fields:**
- `accountNo`, `meterNo`
- `customerName`, `contactNo`
- `installationAddress`, `feederName`, `SDName`
- `installationDate`, `registerDate`
- `phaseType`, `sanctionLoad`
- `tariffSolution`, `meterModel`, `transformer`

### 3. Daily Consumption

**Path:**
```
GET /:type/customer/getCustomerDailyConsumption?accountNo=...&dateFrom=...&dateTo=...
```

**Query Parameters:**
| Parameter | Type   | Required | Description                  |
|-----------|--------|----------|------------------------------|
| `accountNo` | string | Yes    | Account number               |
| `dateFrom`  | string | Yes    | Start date `YYYY-MM-DD`      |
| `dateTo`    | string | Yes    | End date `YYYY-MM-DD`        |

**Response `data`:** Array of daily records.

**Key fields per record:**
- `date`
- `consumedUnit` (kWh / units)
- `consumedTaka` (cost in BDT)
- `accountNo`, `meterNo`
- `customerName`, `installationAddress`
- `phaseType`, `sanctionLoad`, `tariffSolution`
- `importReactiveEnergyIncrement`

**Note:** The raw data is often cumulative. Callers frequently post-process it to compute daily deltas.

### 4. Monthly Consumption

**Path:**
```
GET /:type/customer/getCustomerMonthlyConsumption?accountNo=...&monthFrom=...&monthTo=...
```

**Query Parameters:**
| Parameter | Type   | Required | Description               |
|-----------|--------|----------|---------------------------|
| `accountNo` | string | Yes    | Account number            |
| `monthFrom` | string | Yes    | Start month `YYYY-MM`     |
| `monthTo`   | string | Yes    | End month `YYYY-MM`       |

**Response `data`:** Array of monthly records.

**Key fields per record:**
- `month` (`YYYY-MM`)
- `consumedUnit`
- `consumedTaka`
- `maximumDemand`
- `APF`
- `accountNo`, `meterNo`, `customerName`, etc.

### 5. Recharge History

**Path:**
```
GET /:type/customer/getRechargeHistory?accountNo=...&dateFrom=...&dateTo=...
```

**Query Parameters:**
| Parameter | Type   | Required | Description                  |
|-----------|--------|----------|------------------------------|
| `accountNo` | string | Yes    | Account number               |
| `dateFrom`  | string | Yes    | Start date `YYYY-MM-DD`      |
| `dateTo`    | string | Yes    | End date `YYYY-MM-DD`        |

**Response `data`:** Array of recharge records.

**Key fields per record:**
- `rechargeDate`
- `totalAmount`, `energyAmount`, `chargeAmount`
- `VAT`
- `rebate`
- `orderID`, `token`, `sequence`
- `rechargeOperator`, `orderStatus`
- `chargeItems` (array of charge breakdowns)

## Date Formats

- Daily / Recharge: `YYYY-MM-DD` (e.g. `2026-05-01`)
- Monthly: `YYYY-MM` (e.g. `2026-05`)

Dates are interpreted in Asia/Dhaka timezone.

## Account Number Format

- Usually numeric (e.g. `123456789`)
- Sometimes prefixed (e.g. `DESCO-123456789`)
- Both forms are commonly accepted — test with your actual bill number.

## Usage Notes & Behavior

- The API returns data for any valid account number you can guess/supply.
- `data: null` or empty array is common even on HTTP 200 when there is no data for the requested range/type.
- Some accounts only work under `unified`, others only under `tkdes`.
- Passing both `accountNo` and `meterNo` on the balance endpoint is supported by some tools.
- No rate limiting is documented (use responsibly).
- Responses can contain personal information (name, address, contact number, meter details).

## Example cURL Commands

```bash
# Balance (unified)
curl "https://prepaid.desco.org.bd/api/unified/customer/getBalance?accountNo=YOUR_ACCOUNT"

# Balance (tkdes)
curl "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance?accountNo=YOUR_ACCOUNT"

# Daily consumption (last 10 days example)
curl "https://prepaid.desco.org.bd/api/unified/customer/getCustomerDailyConsumption?accountNo=YOUR_ACCOUNT&dateFrom=2026-05-20&dateTo=2026-05-30"

# Monthly consumption
curl "https://prepaid.desco.org.bd/api/tkdes/customer/getCustomerMonthlyConsumption?accountNo=YOUR_ACCOUNT&monthFrom=2025-06&monthTo=2026-05"

# Recharge history
curl "https://prepaid.desco.org.bd/api/unified/customer/getRechargeHistory?accountNo=YOUR_ACCOUNT&dateFrom=2025-01-01&dateTo=2026-05-30"

# Customer info
curl "https://prepaid.desco.org.bd/api/tkdes/customer/getCustomerInfo?accountNo=YOUR_ACCOUNT"
```

## Sample Responses

### Balance (successful)
```json
{
  "code": 200,
  "desc": "OK",
  "data": {
    "accountNo": "987654321",
    "meterNo": "667788990011",
    "balance": 1384.35,
    "currentMonthConsumption": 2020.49,
    "readingTime": "2022-07-19 00:00:00"
  }
}
```

### Customer Info
```json
{
  "code": 200,
  "desc": "OK",
  "data": {
    "accountNo": "987654321",
    "contactNo": "01833000000",
    "customerName": "MR. JOHN DOE",
    "feederName": "Sector 11",
    "installationAddress": "H-42, R-7, SEC-13, UTTARA",
    "installationDate": "2019-06-23 00:00:00",
    "meterNo": "667788990011",
    "phaseType": "Single Phase Meter",
    "registerDate": "2019-06-23 00:00:00",
    "sanctionLoad": 6,
    "tariffSolution": "Category-A: Residential",
    "meterModel": null,
    "transformer": null,
    "SDName": "Turag"
  }
}
```

### Error (account not found on this type)
```json
{
  "code": 16001,
  "desc": "The Account No. does not exist",
  "data": null
}
```

This is the complete functional picture of the publicly accessible DESCO prepaid meter API based on observed usage across multiple independent implementations.
