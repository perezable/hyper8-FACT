# VAPI Integration Guide for FACT Knowledge Base

## Architecture Overview

FACT serves as the intelligent knowledge retrieval system for VAPI voice agents handling contractor licensing calls. The integration follows this flow:

```
[VAPI Voice Agent] → [FACT API] → [Knowledge Base] → [Response]
         ↓                ↑
    [Telephony]      [Real-time Data]
```

## Key Integration Points

### 1. Knowledge Retrieval Endpoint for VAPI

VAPI agents will primarily use the knowledge search endpoint to retrieve contextual information during calls.

#### Primary Endpoint: Knowledge Search
```
POST https://hyper8-fact-fact-system.up.railway.app/knowledge/search
```

**Request Body:**
```json
{
  "query": "Georgia contractor license requirements",
  "category": "state_licensing_requirements",
  "state": "GA",
  "difficulty": "basic",
  "limit": 3
}
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "question": "Georgia Contractor License Requirements",
      "answer": "Georgia requires contractors to be licensed for work over $2,500...",
      "category": "state_licensing_requirements",
      "tags": "georgia,general_contractor,license_requirements",
      "state": "GA",
      "priority": "normal",
      "difficulty": "basic"
    }
  ],
  "total_count": 1,
  "query": "Georgia contractor license requirements",
  "timestamp": "2025-09-09T20:00:00Z"
}
```

### 2. Persona Detection for VAPI Squads

VAPI squads can route calls to specialized agents based on detected personas.

#### Endpoint: Persona Detection
```
POST https://hyper8-fact-fact-system.up.railway.app/api/v1/knowledge/persona/detect
```

**Request Body:**
```json
{
  "conversation_text": "I'm overwhelmed with all these requirements and don't know where to start",
  "confidence_threshold": 0.7
}
```

**Response:**
```json
{
  "detected_persona": "overwhelmed_veteran",
  "confidence": 0.85,
  "response_adjustments": {
    "empathy_level": "high",
    "pace": "slower",
    "detail_level": "comprehensive"
  },
  "detection_signals": ["Stress indicators present"]
}
```

### 3. Trust Score Tracking

Track trust throughout the conversation for dynamic response adjustment.

#### Endpoint: Trust Calculation
```
POST https://hyper8-fact-fact-system.up.railway.app/api/v1/knowledge/trust/calculate
```

**Request Body:**
```json
{
  "call_id": "vapi_call_123",
  "events": [
    {"type": "positive", "weight": 1.5, "description": "User engaged with question"},
    {"type": "negative", "weight": 1.0, "description": "User expressed price concern"}
  ],
  "current_score": 45.0
}
```

### 4. State Requirements Lookup

Quick access to state-specific licensing information.

#### Endpoint: State Requirements
```
GET https://hyper8-fact-fact-system.up.railway.app/api/v1/knowledge/states/{state_code}/requirements
```

**Response:**
```json
{
  "state_code": "GA",
  "state_name": "Georgia",
  "requirements": [...],
  "summary": "Georgia requires contractors to be licensed for work over $2,500...",
  "metadata": {
    "regulatory_body": "Georgia State Licensing Board",
    "processing_timeline": "4-6 weeks"
  }
}
```

## VAPI Configuration Examples

### 1. VAPI Assistant Configuration with FACT Integration

```javascript
// VAPI Assistant Configuration
const assistant = {
  name: "CLP Licensing Expert",
  firstMessage: "Hi! I'm here to help you with contractor licensing. What state are you interested in?",
  model: {
    provider: "openai",
    model: "gpt-4",
    temperature: 0.7
  },
  voice: {
    provider: "elevenlabs",
    voiceId: "emily"
  },
  functions: [
    {
      name: "searchKnowledge",
      description: "Search FACT knowledge base for contractor licensing information",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string" },
          state: { type: "string" },
          category: { type: "string" }
        }
      },
      serverUrl: "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"
    }
  ]
};
```

### 2. VAPI Squad Configuration for Persona-Based Routing

```javascript
// VAPI Squad Configuration
const squad = {
  name: "CLP Expert Squad",
  members: [
    {
      assistantId: "asst_overwhelmed_veteran_specialist",
      transferCondition: "persona === 'overwhelmed_veteran'",
      description: "Specialist for overwhelmed veterans"
    },
    {
      assistantId: "asst_newcomer_guide",
      transferCondition: "persona === 'confused_newcomer'",
      description: "Guide for confused newcomers"
    },
    {
      assistantId: "asst_general_expert",
      transferCondition: "default",
      description: "General licensing expert"
    }
  ],
  initialAssistantId: "asst_persona_detector"
};
```

## Webhook Endpoint for VAPI Functions

FACT provides a unified webhook endpoint for VAPI function calls:

```
POST https://hyper8-fact-fact-system.up.railway.app/vapi/webhook
```

### Webhook Request Format (from VAPI):
```json
{
  "message": {
    "type": "function-call",
    "functionCall": {
      "name": "searchKnowledge",
      "parameters": {
        "query": "Georgia license requirements",
        "state": "GA"
      }
    }
  },
  "call": {
    "id": "call_123",
    "assistantId": "asst_456"
  }
}
```

### Webhook Response Format (to VAPI):
```json
{
  "result": {
    "answer": "Georgia requires contractors to be licensed for work over $2,500. General contractor license requires 4 years experience...",
    "source": "knowledge_base",
    "confidence": 0.95,
    "metadata": {
      "category": "state_licensing_requirements",
      "state": "GA"
    }
  }
}
```

## Best Practices for VAPI Integration

### 1. Caching Strategy
- Cache frequently requested state requirements
- Store persona detection results for call duration
- Cache trust scores with 30-second TTL

### 2. Rate Limiting
- FACT API supports 100 requests/minute per IP
- Implement exponential backoff for retries
- Use webhook batching where possible

### 3. Error Handling
```javascript
try {
  const response = await fetch('https://hyper8-fact-fact-system.up.railway.app/knowledge/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    // Fallback to general response
    return getDefaultResponse(query);
  }
  
  return await response.json();
} catch (error) {
  console.error('FACT API error:', error);
  return getDefaultResponse(query);
}
```

### 4. Performance Optimization
- Use specific categories to narrow search
- Limit results to 3-5 for voice responses
- Pre-fetch common queries during call setup

## Monitoring & Analytics

### Call Analytics Endpoint
```
GET https://hyper8-fact-fact-system.up.railway.app/api/v1/knowledge/analytics/conversation/{call_id}
```

Track:
- Persona detection accuracy
- Trust score progression
- Knowledge queries per call
- Objections handled
- Call outcomes

## Environment Variables for VAPI

```env
# VAPI Configuration
FACT_API_URL=https://hyper8-fact-fact-system.up.railway.app
FACT_API_KEY=your_api_key_here  # If authentication is enabled
VAPI_WEBHOOK_SECRET=your_webhook_secret
```

## Testing with VAPI

### 1. Test Knowledge Retrieval
```bash
curl -X POST https://hyper8-fact-fact-system.up.railway.app/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contractor license Georgia",
    "limit": 3
  }'
```

### 2. Test Persona Detection
```bash
curl -X POST https://hyper8-fact-fact-system.up.railway.app/api/v1/knowledge/persona/detect \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_text": "I am so confused about where to start",
    "confidence_threshold": 0.7
  }'
```

## Support & Documentation

- FACT API Status: https://hyper8-fact-fact-system.up.railway.app/health
- Knowledge Stats: https://hyper8-fact-fact-system.up.railway.app/knowledge/stats
- Categories: https://hyper8-fact-fact-system.up.railway.app/knowledge/categories

## Next Steps

1. Configure VAPI assistants with FACT webhook URL
2. Set up squad routing based on persona detection
3. Implement trust-based conversation adjustments
4. Monitor call analytics for optimization
5. Train agents on knowledge base responses

---

*FACT + VAPI = Intelligent AI Voice Agents for Contractor Licensing*