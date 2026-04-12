# 🚀 Quick Start Guide

## For Existing Deployment

Your system is already running at: **https://lead-conversion-system.onrender.com**

### Test Client ID
```
00814277-181b-47a1-94e5-e04827edaa2f
```

### Test the System

#### 1. Test Webhook (creates a lead + sends email)
```bash
curl -X POST https://lead-conversion-system.onrender.com/webhook/new-lead \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "00814277-181b-47a1-94e5-e04827edaa2f",
    "name": "Your Name",
    "email": "your@email.com",
    "message": "Hello, I am interested in your services!"
  }'
```

#### 2. Check Leads
- Dashboard: https://lead-conversion-system.onrender.com/dashboard
- API: https://lead-conversion-system.onrender.com/leads

#### 3. Test Email
- Visit: https://lead-conversion-system.onrender.com/test-email

---

## How to Integrate with Your Website

### Option 1: HTML Form
```html
<form action="https://lead-conversion-system.onrender.com/webhook/new-lead" method="POST">
  <input type="text" name="name" placeholder="Your Name" required>
  <input type="email" name="email" placeholder="Your Email" required>
  <input type="hidden" name="client_id" value="00814277-181b-47a1-94e5-e04827edaa2f">
  <textarea name="message" placeholder="Your Message" required></textarea>
  <button type="submit">Send</button>
</form>
```

### Option 2: JavaScript Fetch
```javascript
async function submitLead(name, email, message) {
  const response = await fetch('https://lead-conversion-system.onrender.com/webhook/new-lead', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: '00814277-181b-47a1-94e5-e04827edaa2f',
      name: name,
      email: email,
      message: message
    })
  });
  return await response.json();
}
```

### Option 3: PHP
```php
<?php
$curl = curl_init();
curl_setopt_array($curl, [
  CURLOPT_URL => 'https://lead-conversion-system.onrender.com/webhook/new-lead',
  CURLOPT_POST => true,
  CURLOPT_POSTFIELDS => json_encode([
    'client_id' => '00814277-181b-47a1-94e5-e04827edaa2f',
    'name' => $_POST['name'],
    'email' => $_POST['email'],
    'message' => $_POST['message']
  ]),
  CURLOPT_HTTPHEADER => ['Content-Type: application/json']
]);
$response = curl_exec($curl);
curl_close($curl);
?>
```

### Option 4: WordPress Contact Form 7
Add this to your Contact Form 7 mail settings:
```
Subject: New Lead from Contact Form
Mail Body:
client_id: 00814277-181b-47a1-94e5-e04827edaa2f
name: [your-name]
email: [your-email]
message: [your-message]

---
This message was sent from your website.
```

---

## Common Tasks

### Create a New Client/Agency
Run this SQL in Supabase:
```sql
INSERT INTO clients (agency_name, email, config)
VALUES ('New Agency', 'agency@email.com', '{}')
RETURNING id;
```

### Reset a Lead's Status
```sql
UPDATE leads SET status = 'new', follow_up_count = 0 WHERE id = 'LEAD_ID';
```

### Delete a Lead
```sql
DELETE FROM leads WHERE id = 'LEAD_ID';
```

### View Recent Leads
```sql
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10;
```

---

## Troubleshooting

### Email not sending?
1. Check Resend dashboard: https://resend.com/emails
2. Verify RESEND_API_KEY is set in Render
3. Check spam folder

### Webhook returning error?
1. Check /health endpoint is working
2. Verify database tables exist
3. Check Render logs for errors

### Need to add columns to leads table?
```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS new_column TEXT;
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase admin key | ✅ |
| `RESEND_API_KEY` | Resend email API key | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | Optional |

---

## Support

- Check logs: Render Dashboard → Your Service → Logs
- Health check: https://lead-conversion-system.onrender.com/health
- Dashboard: https://lead-conversion-system.onrender.com/dashboard
