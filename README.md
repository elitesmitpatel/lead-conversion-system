# Lead Conversion System

AI-powered lead conversion system with 4 specialized agents. Built for marketing agencies to automatically respond to leads, follow up intelligently, and reactivate dead leads.

## 🌐 Live Demo
- **Dashboard:** https://your-app.onrender.com/dashboard
- **API Health:** https://your-app.onrender.com/health

## 🎯 Features

| Feature | Description |
|---------|-------------|
| **Speed-to-Lead** | Responds to every new lead in under 60 seconds |
| **Follow-Up Engine** | 10 automated follow-ups over 14-21 days |
| **Database Reactivation** | Re-engages cold leads with fresh offers |
| **CRM Integration** | Full pipeline visibility and analytics |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LEAD CONVERSION SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Webhook   │  │  Chat API   │  │   CRM API   │          │
│  │   (Leads)   │  │  (Widget)   │  │ (Dashboard) │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         ▼                                    │
│              ┌─────────────────────┐                         │
│              │   LANGGRAPH         │                         │
│              │   ORCHESTRATOR       │                         │
│              └──────────┬──────────┘                         │
│                         │                                    │
│    ┌────────────────────┼────────────────────┐             │
│    │                    │                    │              │
│    ▼                    ▼                    ▼              │
│ ┌──────────┐    ┌──────────────┐    ┌────────────────┐   │
│ │ Speed-to- │    │ Follow-Up    │    │  Reactivation  │   │
│ │   Lead    │    │   Engine     │    │    Agent       │   │
│ └─────┬─────┘    └──────┬───────┘    └───────┬────────┘   │
│       │                 │                    │              │
│       └─────────────────┼────────────────────┘              │
│                         ▼                                    │
│              ┌─────────────────────┐                         │
│              │     SUPABASE        │                         │
│              │   (PostgreSQL)      │                         │
│              └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 💰 Free Stack

| Service | Free Tier | Purpose |
|---------|-----------|---------|
| **Render** | 750 hrs/mo | Python API hosting |
| **Supabase** | 500MB | PostgreSQL database |
| **Google Gemini** | 15 RPM | AI responses |
| **Resend** | 100/day | Email sending |
| **Twilio** | $15 trial | SMS (optional) |

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/your-username/lead-conversion-system.git
cd lead-conversion-system
pip install -r requirements.txt
```

### 2. Set Up Supabase
- Create project at [supabase.com](https://supabase.com)
- Run `supabase/schema.sql` in SQL Editor

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your keys
```

### 4. Run Locally
```bash
uvicorn main:app --reload
# Visit http://localhost:8000
```

### 5. Deploy to Render
- Connect GitHub repo to Render
- Add environment variables
- Deploy!

## 📁 Project Structure

```
lead-conversion-system/
├── main.py                    # FastAPI app entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── deploy.md                 # Deployment guide
│
├── agents/                   # AI Agent implementations
│   ├── orchestrator.py      # LangGraph routing
│   ├── speed_to_lead.py     # Agent 1: Auto-response
│   ├── follow_up_engine.py  # Agent 2: Follow-up sequences
│   ├── database_reactivation.py  # Agent 3: Reactivation
│   ├── crm_integration.py    # Agent 4: CRM sync
│   ├── scoring.py           # Interest score tracking
│   └── scheduler.py          # Background tasks
│
├── integrations/             # External service integrations
│   ├── supabase_client.py   # Database operations
│   ├── email.py             # Resend email API
│   └── sms.py               # Twilio SMS API
│
├── dashboard/               # Frontend
│   ├── crm-dashboard.html   # CRM dashboard
│   └── chat-widget.html     # Embeddable chat widget
│
├── api/                     # Additional API routes
└── supabase/
    └── schema.sql           # Database schema
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/new-lead` | POST | Receive new leads |
| `/chat` | POST | Handle chat widget messages |
| `/api/dashboard/{client_id}` | GET | Dashboard metrics |
| `/api/leads/{client_id}` | GET | List leads |
| `/api/lead/{lead_id}` | GET | Lead details |
| `/api/lead/{lead_id}` | PATCH | Update lead |
| `/api/clients/onboard` | POST | Onboard new client |
| `/health` | GET | Health check |

## 💬 Chat Widget Integration

```html
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'https://your-app.com/widget.js?key=YOUR_CLIENT_KEY';
    script.async = true;
    document.head.appendChild(script);
  })();
</script>
```

## 📊 Dashboard

Access the visual CRM at: `https://your-app.com/dashboard?client=YOUR_API_KEY`

Features:
- Pipeline view with 5 stages
- Real-time metrics
- Lead activity feed
- Interest scoring

## 🤖 How It Works

### Speed-to-Lead Agent
1. New lead comes in via webhook
2. AI generates personalized response using Gemini
3. Sends via email/SMS/chat
4. Logs to database and updates status

### Follow-Up Engine
1. Scheduler checks hourly for due follow-ups
2. Generates context-aware follow-up message
3. Adjusts tone based on interest score
4. Updates next follow-up time

### Reactivation Agent
1. Runs weekly on dead leads
2. Generates reactivation offer
3. Re-engages with fresh value
4. Moves back to follow-up sequence

## 🔧 Configuration

Required environment variables:
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GEMINI_API_KEY=AIza...
RESEND_API_KEY=re_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
```

## 📝 License
MIT License - Use freely for your projects!

## 👤 Author
Built for marketing agencies to stop losing leads.

---
⭐ Star this repo if it helps you!