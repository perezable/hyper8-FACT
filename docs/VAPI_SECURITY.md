# VAPI Webhook Security Guide

## Current Status

### Webhook URLs
Your FACT system exposes these webhooks:
- **Main Webhook**: `https://hyper8-fact-fact-system.up.railway.app/vapi/webhook`
- **Call Status**: `https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/call-status`
- **Health Check**: `https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health`

### Current Security Level: ⚠️ BASIC
- ✅ HTTPS/TLS encryption (provided by Railway)
- ✅ Input validation with Pydantic
- ✅ Basic SQL injection protection
- ❌ No authentication
- ❌ No request verification
- ❌ No rate limiting
- ❌ Open CORS policy

## Implementing Security

### 1. VAPI Webhook Signature Verification

VAPI can sign webhooks with a secret key. To enable:

1. Get your webhook secret from VAPI Dashboard
2. Set environment variable in Railway:
```bash
VAPI_WEBHOOK_SECRET=your_secret_here
```

3. The security module will automatically verify signatures

### 2. API Key Authentication

Add an additional layer with API keys:

```bash
VAPI_API_KEYS=key1,key2,key3
```

Then configure VAPI to send the API key in headers:
```javascript
// In VAPI function configuration
headers: {
  "X-API-Key": "your_api_key"
}
```

### 3. IP Whitelisting

Restrict access to VAPI's IP addresses only:

```bash
# Get current VAPI IPs from their documentation
VAPI_ALLOWED_IPS=52.53.204.78,54.183.205.110
```

### 4. Rate Limiting

Prevent abuse with rate limiting:

```bash
VAPI_RATE_LIMIT=true
VAPI_MAX_REQUESTS=100  # Per minute per IP
```

## Setting Up in Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add these environment variables:

```env
VAPI_WEBHOOK_SECRET=<get-from-vapi-dashboard>
VAPI_RATE_LIMIT=true
VAPI_MAX_REQUESTS=100
CORS_ORIGINS=https://api.vapi.ai
```

## Testing Security

### Test Webhook Signature
```bash
# With valid signature
curl -X POST https://hyper8-fact-fact-system.up.railway.app/vapi/webhook \
  -H "Content-Type: application/json" \
  -H "X-Vapi-Signature: <valid-signature>" \
  -d '{"message": {"type": "function-call"}}'

# Should fail without signature (if configured)
curl -X POST https://hyper8-fact-fact-system.up.railway.app/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"type": "function-call"}}'
```

### Test Rate Limiting
```bash
# Run this multiple times quickly
for i in {1..150}; do
  curl -X POST https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health
done
# Should get 429 errors after 100 requests
```

## VAPI Configuration

In your VAPI assistant configuration, ensure the webhook URL is set correctly:

```javascript
{
  functions: [
    {
      name: "searchKnowledge",
      serverUrl: "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook",
      // Optional: Add authentication header
      headers: {
        "X-API-Key": "your_secure_api_key"
      }
    }
  ]
}
```

## Security Best Practices

### DO:
- ✅ Use webhook signatures from VAPI
- ✅ Implement rate limiting
- ✅ Monitor webhook logs for suspicious activity
- ✅ Use environment variables for secrets
- ✅ Regularly rotate API keys

### DON'T:
- ❌ Hardcode secrets in code
- ❌ Log sensitive data (phone numbers, personal info)
- ❌ Allow unlimited requests
- ❌ Skip HTTPS (Railway handles this)

## Monitoring

Check your webhook health:
```bash
curl https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health
```

Response:
```json
{
  "status": "healthy",
  "endpoint": "VAPI Webhook Handler",
  "cache_size": 0,
  "timestamp": "2025-09-09T20:00:00Z"
}
```

## Troubleshooting

### 401 Unauthorized
- Check webhook secret matches VAPI dashboard
- Verify API key is correct

### 429 Too Many Requests
- Rate limit exceeded
- Increase VAPI_MAX_REQUESTS or implement caching

### 403 Forbidden
- IP not in whitelist
- Check VAPI's current IP addresses

## Current Recommendation

For your use case, implement at minimum:
1. **Webhook signature verification** (most important)
2. **Rate limiting** (prevent abuse)
3. **Tighten CORS** to only allow VAPI domains

This provides good security without overcomplicating the system.