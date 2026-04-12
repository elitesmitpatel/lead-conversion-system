# Lead Conversion System

AI-powered lead management system for marketing agencies. Automatically responds to leads, follows up, and tracks engagement.

## 🚀 Live URLs

| Resource | URL |
|----------|-----|
| **Live App** | https://lead-conversion-system.onrender.com |
| **Dashboard** | https://lead-conversion-system.onrender.com/dashboard |
| **Health Check** | https://lead-conversion-system.onrender.com/health |
| **API (Leads)** | https://lead-conversion-system.onrender.com/leads |

## ✨ Features

- **Auto-Response** - Sends personalized email within seconds of lead submission
- **Lead Tracking** - All leads saved to database with status updates
- **Dashboard** - Real-time view of all leads and metrics
- **Interest Scoring** - Track lead engagement (0-100 score)
- **Follow-up Ready** - System prepared for automated follow-up sequences

## 📁 Project Structure

```
lead-conversion-system/
├── main.py                    # FastAPI app - webhook, API endpoints, dashboard
├── requirements.txt           # Python dependencies
├── render.yaml              # Render deployment config (web + worker)
├── Procfile                # Alternative deployment config
├── .env.example            # Environment variables template
│
├── integrations/            # External service integrations
│   ├── supabase_client.py # Database operations
│   ├── email.py          # Email sending (Resend)
│   └── sms.py            # SMS sending (Twilio)
│
├── agents/                 # AI Agent system (LangGraph)
│   ├── orchestrator.py   # Routes leads to appropriate agents
│   ├── speed_to_lead.py  # First response agent
│   ├── follow_up_engine.py # Follow-up sequence agent
│   ├── database_reactivation.py # Dead lead reactivation
│   ├── scoring.py       # Interest score tracking
│   ├── scheduler.py      # Background job scheduler
│   └── __main__.py      # Worker entry point
│
├── dashboard/             # Frontend UI
│   └── crm-dashboard.html # Full CRM dashboard
│
├── scripts/               # Utility scripts
│   ├── setup_database.sql # Database schema
│   └── setup_test_client.py # Create test client
│
└── supabase/
    └── schema.sql       # Complete database schema
```

## 💰 Free Stack

| Service | Free Tier | Purpose |
|---------|-----------|---------|
| **Render** | 750 hrs/mo | Python API hosting |
| **Supabase** | 500MB | PostgreSQL database |
| **Google Gemini** | 15 RPM | AI responses |
| **Resend** | 100/day | Email sending |
| **Twilio** | $15 trial | SMS (optional) |

## 🔑 API Keys Needed

| Service | Key Name | Purpose |
|---------|----------|---------|
| Supabase | `SUPABASE_URL` | Database connection |
| Supabase | `SUPABASE_SERVICE_ROLE_KEY` | Admin database access |
| Google Gemini | `GEMINI_API_KEY` | AI response generation |
| Resend | `RESEND_API_KEY` | Email sending |
| Twilio | `TWILIO_ACCOUNT_SID` | SMS (optional) |
| Twilio | `TWILIO_AUTH_TOKEN` | SMS auth (optional) |
| Twilio | `TWILIO_PHONE_NUMBER` | SMS from number (optional) |

## 🌐 API Endpoints

### Lead Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/new-lead` | POST | Receive new lead → save + send email |
| `/leads` | GET | Get all leads |
| `/leads/{id}/followup` | POST | Manually trigger follow-up |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/test-email` | GET | Test email sending |
| `/dashboard` | GET | CRM dashboard UI |
| `/` | GET | Root page |

## 📝 Webhook Payload Format

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "source": "website",
  "message": "I'm interested in your services"
}
```

### Required Fields:
- `client_id` - Your client/agency ID (UUID)
- `name` - Lead's name
- `email` - Lead's email address
- `message` - Lead's message

### Optional Fields:
- `phone` - Lead's phone number
- `source` - Where lead came from (default: "website")

## 🗄️ Database Schema

### clients Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `agency_name` | TEXT | Agency name |
| `email` | TEXT | Contact email |
| `config` | JSONB | Settings |

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
| `status` | TEXT | new, contacted, nurturing, dead, booked, won, lost |
| `interest_score` | INT | 0-100 engagement score |
| `follow_up_count` | INT | Number of follow-ups sent |
| `last_contact` | TIMESTAMPTZ | Last interaction timestamp |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

### conversations Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `lead_id` | UUID | Foreign key to leads |
| `role` | TEXT | user, assistant |
| `content` | TEXT | Message content |
| `channel` | TEXT | email, sms, chat |
| `strategy` | TEXT | Follow-up strategy used |

### events Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `lead_id` | UUID | Foreign key to leads |
| `event_type` | TEXT | Type of event |
| `metadata` | JSONB | Additional data |

## 🚀 Deployment

### Render (Recommended)

1. Push to GitHub
2. Connect repo to Render
3. Add environment variables
4. Deploy!

See [deploy.md](deploy.md) for detailed instructions.

## 🧪 Testing

### Test Client ID
```
00814277-181b-47a1-94e5-e04827edaa2f
```

### Test Webhook
```bash
curl -X POST https://lead-conversion-system.onrender.com/webhook/new-lead \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "00814277-181b-47a1-94e5-e04827edaa2f",
    "name": "Test Lead",
    "email": "test@example.com",
    "message": "Hello!"
  }'
```

## 📊 How It Works

```
1. Lead Submits Form
        ↓
2. POST /webhook/new-lead
        ↓
3. Lead Saved to Database (Supabase)
        ↓
4. Status Updated: "new" → "contacted"
        ↓
5. Auto-Email Sent (Resend)
        ↓
6. Lead Appears in Dashboard
```

## 🔧 Troubleshooting

### Email not sending?
- Check RESEND_API_KEY is set in Render environment
- Check Resend dashboard for sent emails
- Check spam folder

### Webhook returning 500?
- Verify database tables exist (run setup_database.sql)
- Check RLS policies are disabled or allow inserts
- Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are correct

### Leads not showing in dashboard?
- Refresh the page
- Check browser console for errors
- Verify /leads endpoint returns data

## 🤖 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LEAD CONVERSION SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Webhook   │  │   Chat     │  │   Dashboard  │         │
│  │   (Leads)   │  │   API      │  │   UI        │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         ▼                                  │
│              ┌─────────────────────┐                       │
│              │      SUPABASE       │                       │
│              │    (PostgreSQL)     │                       │
│              └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## 📝 License

MIT License - Use freely!

---

⭐ Star this repo if it helps you!
