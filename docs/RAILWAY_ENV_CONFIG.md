# Railway Environment Configuration Guide

## Security Configuration Levels

### Level 0: Testing (Default - Current State)
No environment variables set. System is open for testing.

```env
# No variables set - open access for testing
```

- ✅ Easy testing from any client
- ✅ No CORS restrictions
- ❌ No security
- ❌ No rate limiting

### Level 1: Basic Security (Recommended Minimum)
Enable webhook signature verification only.

```env
# Webhook signature (activates security automatically)
VAPI_WEBHOOK_SECRET=a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb
```

- ✅ Webhook signature verification
- ✅ Still allows any origin (CORS open)
- ✅ Good for testing with VAPI
- ❌ No rate limiting

### Level 2: Add Rate Limiting
Prevent abuse while keeping CORS open.

```env
# Previous settings plus:
VAPI_RATE_LIMIT=true
VAPI_MAX_REQUESTS=100
```

- ✅ Webhook signature verification
- ✅ Rate limiting (100 req/min)
- ✅ Still allows any origin (CORS open)
- ✅ Protection from abuse

### Level 3: Production Security (Full Lockdown)
Complete security with CORS restrictions.

```env
# All security features
VAPI_WEBHOOK_SECRET=a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb
VAPI_RATE_LIMIT=true
VAPI_MAX_REQUESTS=100

# Restrict CORS to VAPI only
CORS_ORIGINS=https://api.vapi.ai,https://dashboard.vapi.ai

# Optional: Additional API keys
VAPI_API_KEYS=backup-key-1,backup-key-2

# Optional: IP whitelist (get VAPI's IPs from their docs)
VAPI_ALLOWED_IPS=
```

- ✅ Full webhook security
- ✅ Rate limiting
- ✅ CORS restrictions
- ✅ Optional API key backup
- ✅ Optional IP whitelist

## How to Configure in Railway

1. Go to your Railway project dashboard
2. Click on your service (hyper8-fact-fact-system)
3. Navigate to "Variables" tab
4. Add the environment variables for your chosen security level
5. Railway will automatically redeploy with new settings

## Testing Your Configuration

### Test if webhook is secured:
```bash
# Should fail without signature
curl -X POST https://hyper8-fact-fact-system.up.railway.app/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"type": "test"}}'
```

### Test with signature (if Level 1+ configured):
```bash
# Should succeed with valid signature
# Use the test script: python tests/test_vapi_security.py
```

### Test CORS (if Level 3 configured):
```javascript
// From browser console on different domain
fetch('https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health')
  .then(r => console.log('CORS allowed'))
  .catch(e => console.log('CORS blocked'))
```

## VAPI Dashboard Configuration

When security is enabled (Level 1+), configure VAPI:

1. Go to VAPI Dashboard
2. Navigate to your Assistant settings
3. Find Webhook/Security configuration
4. Add the webhook secret: `a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb`
5. VAPI will sign all webhook requests with this secret

## Troubleshooting

### "401 Unauthorized" errors
- Check webhook secret matches between Railway and VAPI
- Verify signature header is being sent by VAPI

### "429 Too Many Requests" errors
- Rate limit exceeded
- Increase VAPI_MAX_REQUESTS or implement caching

### CORS errors in browser
- Only occurs with Level 3 security
- Add your domain to CORS_ORIGINS
- Or temporarily remove CORS_ORIGINS for testing

### Testing without restrictions
- Don't set any environment variables
- System defaults to open access
- Add security incrementally as needed

## Security Status Endpoint

Check current security status:
```bash
curl https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health
```

Returns:
- `status`: "healthy" if running
- `timestamp`: Current time
- No sensitive data exposed

## Recommended Progression

1. **Start**: No variables (testing)
2. **Development**: Level 1 (signature only)
3. **Staging**: Level 2 (add rate limiting)
4. **Production**: Level 3 (full security)

This allows you to test freely while gradually adding security layers.