# Render Deployment Configuration

## Option 1: render.yaml (Recommended for Render)
```yaml
services:
  - type: web
    name: lead-conversion-system
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        value: your-supabase-url
      - key: SUPABASE_SERVICE_ROLE_KEY
        value: your-service-role-key
      - key: GEMINI_API_KEY
        value: your-gemini-key
      - key: RESEND_API_KEY
        value: re_xxx
      - key: TWILIO_ACCOUNT_SID
        value: your-twilio-sid
      - key: TWILIO_AUTH_TOKEN
        value: your-twilio-token
```

## Option 2: Procfile (Alternative)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: python -c "import asyncio; from agents.scheduler import setup_scheduler; s=setup_scheduler(); s.start()"
```

## Option 3: Dockerfile (For Docker deployment)
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Deployment Steps for Render:

1. **Push code to GitHub**
   ```bash
   cd lead-conversion-system
   git init
   git add .
   git commit -m "Initial commit - Lead Conversion System"
   git remote add origin https://github.com/your-username/lead-conversion-system.git
   git push -u origin main
   ```

2. **Create Render Account** (Free)
   - Go to render.com
   - Sign up with GitHub

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - Name: lead-conversion-system
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Go to "Environment" tab
   - Add all required variables:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_ROLE_KEY`
     - `GEMINI_API_KEY`
     - `RESEND_API_KEY` (optional)
     - `TWILIO_ACCOUNT_SID` (optional)
     - `TWILIO_AUTH_TOKEN` (optional)
     - `TWILIO_PHONE_NUMBER` (optional)

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Get your URL

## Free Tier Limits:
- **Render Free**: 750 hours/month, sleeps after 15 min inactivity
- **Supabase Free**: 500MB database, 50MB file storage
- **Gemini Free**: 15 requests/minute, 1M context
- **Resend Free**: 100 emails/day
- **Twilio Trial**: $15 credit for testing

## Testing Your Deployment:

```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Test webhook
curl -X POST https://your-app.onrender.com/webhook/new-lead \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client-id",
    "name": "Test Lead",
    "email": "test@example.com",
    "message": "Interested in services"
  }'
```

## Architecture Overview:

```
                    ┌─────────────────┐
                    │   Render Free   │
                    │   (Python/Fast   │
                    │     API)         │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌────────────┐   ┌──────────────┐   ┌─────────────┐
    │  Supabase  │   │   Gemini     │   │   Resend    │
    │ (Database) │   │  (AI/LLM)    │   │  (Email)    │
    └────────────┘   └──────────────┘   └─────────────┘
```

## Support:
- Render Documentation: https://render.com/docs
- Supabase Documentation: https://supabase.com/docs
- FastAPI Documentation: https://fastapi.tiangolo.com/