# API Documentation

Complete reference for all Lead Conversion System API endpoints.

## Base URL
```
https://lead-conversion-system.onrender.com
```

---

## Lead Endpoints

### POST /webhook/new-lead

**Description:** Receive a new lead, save to database, and send auto-response email.

**Request:**
```json
POST /webhook/new-lead
Content-Type: application/json

{
  "client_id": "00814277-181b-47a1-94e5-e04827edaa2f",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "source": "website",
  "message": "I'm interested in your services"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | string (UUID) | ✅ Yes | Your agency/client ID |
| `name` | string | ✅ Yes | Lead's full name |
| `email` | string | ✅ Yes | Lead's email address |
| `phone` | string | No | Lead's phone number |
| `source` | string | No | Where lead came from (default: "website") |
| `message` | string | ✅ Yes | Lead's inquiry message |

**Response (Success):**
```json
{
  "status": "processed",
  "lead_id": "abc123...",
  "email_sent": true,
  "message": "Lead received! Email sent."
}
```

**Response (Error):**
```json
{
  "status": "error",
  "detail": "Error message here"
}
```

---

### GET /leads

**Description:** Retrieve all leads from the database.

**Request:**
```
GET /leads
```

**Response:**
```json
{
  "leads": [
    {
      "id": "abc123...",
      "client_id": "00814277-181b-47a1-94e5-e04827edaa2f",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "source": "website",
      "original_message": "I'm interested...",
      "channel": "email",
      "status": "contacted",
      "interest_score": 50,
      "follow_up_count": 0,
      "last_contact": "2024-01-01T12:00:00Z",
      "created_at": "2024-01-01T11:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

---

### POST /leads/{id}/followup

**Description:** Manually trigger a follow-up email for a specific lead.

**Request:**
```
POST /leads/{lead_id}/followup
```

**Response:**
```json
{
  "status": "sent",
  "result": { ... }
}
```

---

## System Endpoints

### GET /health

**Description:** Check if the API is running.

**Request:**
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.1"
}
```

---

### GET /test-email

**Description:** Send a test email to elitesmit@gmail.com

**Request:**
```
GET /test-email
```

**Response:**
```json
{
  "success": true,
  "id": "email_id_from_resend"
}
```

---

### GET /dashboard

**Description:** Get the CRM dashboard HTML page.

**Request:**
```
GET /dashboard
```

**Response:** HTML page with real-time lead data.

---

### GET /

**Description:** Root page with links to dashboard.

**Request:**
```
GET /
```

**Response:** HTML page with links.

---

## Database Schema

### clients Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `agency_name` | TEXT | Agency name |
| `email` | TEXT | Contact email |
| `phone` | TEXT | Phone number |
| `api_key` | TEXT | Unique API key |
| `calcom_link` | TEXT | Booking link |
| `config` | JSONB | Configuration settings |
| `is_active` | BOOLEAN | Is client active |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### leads Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `client_id` | UUID | Foreign key to clients |
| `name` | TEXT | Lead's name |
| `email` | TEXT | Lead's email |
| `phone` | TEXT | Lead's phone |
| `source` | TEXT | Where lead came from |
| `original_message` | TEXT | Lead's message |
| `channel` | TEXT | email, sms, chat |
| `status` | TEXT | new, contacted, nurturing, dead, booked, won, lost |
| `interest_score` | INT | 0-100 engagement score |
| `follow_up_count` | INT | Number of follow-ups |
| `last_contact` | TIMESTAMPTZ | Last interaction |
| `next_followup_at` | TIMESTAMPTZ | Next follow-up scheduled |
| `booked_at` | TIMESTAMPTZ | When lead booked |
| `deal_value` | DECIMAL | Potential deal value |
| `notes` | TEXT | Internal notes |
| `metadata` | JSONB | Additional data |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### conversations Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `lead_id` | UUID | Foreign key to leads |
| `role` | TEXT | user, assistant |
| `content` | TEXT | Message content |
| `channel` | TEXT | email, sms, chat |
| `strategy` | TEXT | Strategy used |
| `metadata` | JSONB | Additional data |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

### events Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `lead_id` | UUID | Foreign key to leads |
| `event_type` | TEXT | Type of event |
| `metadata` | JSONB | Event data |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

---

## Status Values

| Status | Description |
|--------|-------------|
| `new` | Just received, not yet contacted |
| `contacted` | Initial response sent |
| `nurturing` | In follow-up sequence |
| `dead` | No response after follow-ups |
| `booked` | Call/meeting scheduled |
| `won` | Successfully converted |
| `lost` | Declined or unsubscribed |

---

## Interest Score (0-100)

| Score Range | Description |
|-------------|-------------|
| 80-100 | Hot - Ready to buy |
| 60-79 | Warm - Actively evaluating |
| 40-59 | Tepid - Need more nurturing |
| 20-39 | Cold - Low engagement |
| 0-19 | Frozen - Likely lost |

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad request - invalid input |
| 404 | Not found - resource doesn't exist |
| 500 | Server error - check error detail |

---

## Rate Limits

- Webhook: No limit (unlimited leads)
- Test Email: Use sparingly
- Database: Subject to Supabase plan limits
