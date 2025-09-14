# Setting up Groq API on Railway

## Steps to configure Railway with Groq API:

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Select the `hyper8-FACT` project

2. **Add Environment Variable**
   - Go to Variables tab
   - Add the following environment variable:
   ```
   GROQ_API_KEY = [Your Groq API key from .env file]
   ```

3. **Verify Other Required Variables**
   Ensure these are also set:
   - `DATABASE_URL` (should already be set by Railway)
   - `REDIS_URL` (if using caching)
   - Any other variables from .env that are needed

4. **Restart the Service**
   - Click on the service
   - Select "Restart" to apply the new environment variables

5. **Verify Deployment**
   - Check the deployment logs for any errors
   - The system should now use Groq instead of Anthropic

## Testing the Groq Integration

After setting up, test with:
```bash
curl -X POST https://hyper8-fact-fact-system.up.railway.app/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is NASCLA certification?"}'
```

## Expected Benefits

- **Speed**: 2-5x faster response times
- **Cost**: Significantly lower per-token costs
- **Reliability**: Better rate limits
- **Model**: Using openai/gpt-oss-120b for high-quality responses

## Troubleshooting

If you see errors about:
- "GROQ_API_KEY not found" - Ensure the environment variable is set
- "Model not found" - The system will automatically use the correct model
- Rate limits - Groq has generous limits, but implement backoff if needed