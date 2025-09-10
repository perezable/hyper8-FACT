# VAPI Integration Testing Guide

## Overview

This guide explains how to test that VAPI can successfully access the FACT knowledge retrieval system. The system provides a webhook endpoint that VAPI can call to search the contractor licensing knowledge base.

## Quick Test

### 1. Test Local Server

First, test with a local server to verify the integration works:

```bash
# Start the local server
python src/web_server.py

# In another terminal, run the local test
python scripts/test_vapi_local.py
```

### 2. Test Railway Deployment

Test the deployed Railway instance:

```bash
# Test Railway endpoints
python scripts/test_railway_endpoints.py

# Run full VAPI integration tests
python scripts/test_vapi_integration.py
```

### 3. Test with cURL

Quick test using cURL to simulate a VAPI webhook call:

```bash
# Local test
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -H "x-vapi-signature: test-signature" \
  -d '{
    "message": {
      "type": "function-call",
      "functionCall": {
        "name": "searchKnowledge",
        "parameters": {
          "query": "Georgia contractor license requirements"
        }
      }
    }
  }'

# Railway test
curl -X POST https://your-app.railway.app/vapi/webhook \
  -H "Content-Type: application/json" \
  -H "x-vapi-signature: test-signature" \
  -d '{
    "message": {
      "type": "function-call",
      "functionCall": {
        "name": "searchKnowledge",
        "parameters": {
          "query": "How much does a license cost?"
        }
      }
    }
  }'
```

## VAPI Configuration

### 1. Add Custom Function

In your VAPI assistant configuration, add the `searchKnowledge` function:

```json
{
  "functions": [
    {
      "name": "searchKnowledge",
      "description": "Search the contractor licensing knowledge base for accurate information",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The user's question about contractor licensing"
          },
          "limit": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 3
          },
          "category": {
            "type": "string",
            "description": "Optional category filter",
            "enum": ["requirements", "cost", "timeline", "exam", "renewal", "reciprocity"]
          },
          "state": {
            "type": "string",
            "description": "Optional US state code filter (e.g., 'GA', 'CA', 'TX')"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### 2. Configure Webhook

Set up the webhook endpoint in VAPI:

```json
{
  "webhook": {
    "url": "https://your-railway-app.railway.app/vapi/webhook",
    "headers": {
      "x-vapi-signature": "your-secret-key"
    }
  }
}
```

### 3. Assistant Prompt

Configure your VAPI assistant to use the knowledge base:

```
You are a helpful assistant for contractor licensing questions. 

When users ask about:
- License requirements
- Costs and fees
- Application processes
- Exam information
- State-specific rules
- Timeline estimates

ALWAYS use the searchKnowledge function to find accurate, up-to-date information from our knowledge base before responding.

Format your responses clearly and mention the specific state if applicable.
```

## Testing Checklist

### ✅ Basic Connectivity
- [ ] Server health check returns 200 OK
- [ ] `/vapi/webhook` endpoint is accessible
- [ ] HMAC signature validation works (if enabled)

### ✅ Search Functionality
- [ ] Simple queries return relevant results
- [ ] Natural language variations work ("What's the damage?" = cost)
- [ ] State-specific queries filter correctly
- [ ] Response time is under 300ms for voice

### ✅ Response Format
- [ ] Response includes question and answer
- [ ] Metadata contains score and confidence
- [ ] Multiple results are returned when available
- [ ] Empty queries are handled gracefully

### ✅ Integration Points
- [ ] VAPI can call the webhook
- [ ] Function parameters are parsed correctly
- [ ] Response format matches VAPI expectations
- [ ] Errors return appropriate status codes

## Test Scenarios

### 1. Basic Requirements Query
```javascript
{
  "query": "What are the requirements for a contractor license in Georgia?"
}
// Expected: Georgia-specific requirements with high confidence
```

### 2. Cost Information
```javascript
{
  "query": "How much does it cost to get licensed?"
}
// Expected: Cost breakdown, possibly multiple states
```

### 3. Colloquial Language
```javascript
{
  "query": "What if I flunk the test?"
}
// Expected: Information about exam retakes
```

### 4. ROI Query
```javascript
{
  "query": "What's the ROI on getting licensed?"
}
// Expected: Return on investment information
```

### 5. Complex Multi-Part
```javascript
{
  "query": "I'm in Texas and want to know about requirements and costs"
}
// Expected: Texas-specific requirements and costs
```

## Performance Metrics

### Target Response Times
- **Excellent**: < 100ms (ideal for voice)
- **Good**: 100-300ms (acceptable for voice)
- **Poor**: > 300ms (may cause delays)

### Accuracy Targets
- **Search Accuracy**: 96.7% (achieved)
- **Confidence Threshold**: > 0.7 for voice responses
- **Fallback Rate**: < 5% (no results found)

## Monitoring & Debugging

### 1. Check Logs

```bash
# Railway logs
railway logs

# Local logs
# Check terminal output where server is running
```

### 2. Test Individual Components

```python
# Test enhanced retriever directly
python scripts/test_enhanced_retriever.py

# Test database connection
python scripts/test_database.py

# Test training system
python scripts/demo_training.py
```

### 3. Common Issues

#### Issue: 404 Not Found
- **Cause**: Server not running or wrong URL
- **Solution**: Verify deployment, check Railway dashboard

#### Issue: No Results
- **Cause**: Database not populated or retriever not initialized
- **Solution**: Run data upload, check enhanced retriever status

#### Issue: Slow Response
- **Cause**: Cold start or large dataset
- **Solution**: Implement caching, optimize indexes

#### Issue: Low Accuracy
- **Cause**: Poor fuzzy matching or weights
- **Solution**: Use training system to improve

## Training & Improvement

### 1. Provide Feedback

```bash
curl -X POST http://localhost:8000/training/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What if I fail the test?",
    "result_id": 123,
    "feedback": "incorrect",
    "expected_answer": "You can retake the exam after a waiting period"
  }'
```

### 2. Check Training Status

```bash
curl http://localhost:8000/training/status
```

### 3. Trigger Retraining

```bash
curl -X POST http://localhost:8000/training/retrain
```

### 4. Export Training Data

```bash
curl -X POST http://localhost:8000/training/export \
  -H "Content-Type: application/json" \
  -d '{"file_path": "training_backup.json"}'
```

## Production Deployment

### 1. Environment Variables

Set these in Railway or your deployment platform:

```bash
DATABASE_URL=postgresql://...  # PostgreSQL connection
VAPI_SECRET=your-secret-key   # HMAC signature secret
CORS_ORIGINS=https://vapi.ai  # CORS configuration
PORT=8000                      # Server port
```

### 2. Database Setup

Ensure PostgreSQL is initialized with data:

```bash
# Upload knowledge base
python scripts/upload_to_railway.py

# Verify data
python scripts/test_railway_comprehensive.py
```

### 3. Security

- Enable HMAC signature validation
- Configure CORS for VAPI only
- Use HTTPS in production
- Rotate secrets regularly

## Integration Verification

### Step-by-Step Test

1. **Start Local Server**
   ```bash
   python src/web_server.py
   ```

2. **Run Local Test**
   ```bash
   python scripts/test_vapi_local.py
   ```
   - Should show 100% success rate
   - Response times < 100ms

3. **Deploy to Railway**
   ```bash
   railway up
   ```

4. **Test Railway**
   ```bash
   python scripts/test_vapi_integration.py
   ```
   - Should match local results
   - May have slightly higher latency

5. **Configure VAPI**
   - Add webhook URL
   - Set up function
   - Test with voice call

6. **Monitor & Train**
   - Check accuracy metrics
   - Collect feedback
   - Improve over time

## Success Criteria

The VAPI integration is working correctly when:

✅ Webhook endpoint responds with 200 OK  
✅ Search queries return relevant results  
✅ Response time is under 300ms  
✅ Accuracy is above 95%  
✅ VAPI can parse responses  
✅ Voice agents get helpful answers  
✅ System learns from feedback  

## Support

For issues or questions:
1. Check logs for errors
2. Run diagnostic tests
3. Verify database has data
4. Ensure enhanced retriever is initialized
5. Review training metrics

The system is designed to continuously improve through the training API, so accuracy will increase over time with usage.