# VAPI Tools Reference Guide

## Complete Tool Inventory (8 Custom Tools)

### Sales Agent Tools (All 8 Available)

1. **searchKnowledge** ✅
   - Purpose: Query 469-entry knowledge base
   - Triggers: "what", "how", "requirements", "process", "cost"
   - Example: "What are Georgia requirements?"

2. **detectPersona** ✅
   - Purpose: Identify caller type (Overwhelmed Veteran, Confused Newcomer, etc.)
   - Triggers: "overwhelmed", "confused", "stressed", "new", "urgent"
   - Example: "I'm so overwhelmed by this process"

3. **calculateTrust** ✅
   - Purpose: Track conversation trust score (0-100)
   - Triggers: Use every 3-4 exchanges
   - Example: After positive responses or agreements

4. **handleObjection** ✅
   - Purpose: Provide specific rebuttals
   - Triggers: "expensive", "need time", "do it myself", "not sure"
   - Example: "That sounds too expensive"

5. **bookAppointment** ✅
   - Purpose: Schedule initial consultation
   - Triggers: "get started", "next step", "interested", "sign up"
   - Example: "How do I get started?"

6. **calculateROI** ✅
   - Purpose: Show specific return on investment
   - Triggers: "how much can I make", "ROI", "worth it", "potential earnings"
   - Example: "What's the return on investment?"

7. **qualifierNetworkAnalysis** ✅
   - Purpose: Analyze $3-6k/month passive income opportunity
   - Triggers: "qualifier network", "passive income", "extra money"
   - Example: "Tell me about the qualifier network"

8. **scheduleConsultation** ✅
   - Purpose: Book expert-level consultation
   - Triggers: "complex situation", "multiple states", "commercial"
   - Example: "I have a complex multi-state situation"

### Expert Agent Tools (4 Primary)

1. **searchKnowledge** - Advanced queries
2. **calculateROI** - Detailed ROI calculations
3. **qualifierNetworkAnalysis** - Deep dive into passive income
4. **scheduleConsultation** - Close high-value deals

## Tool Call Flow

```
Customer Speech → Agent Analysis → Tool Selection → Webhook Call → Database Query → Response
```

## Testing Each Tool

### Test searchKnowledge:
- "What are the requirements in Georgia?"
- "How much does the license cost?"
- "What's the application process?"

### Test detectPersona:
- "I'm completely overwhelmed by all this paperwork"
- "I'm new to contracting"
- "I need this done urgently"

### Test calculateTrust:
- Have a 3-4 exchange conversation
- Agent should automatically track trust

### Test handleObjection:
- "That seems really expensive"
- "I need to think about it"
- "I can probably do this myself"

### Test bookAppointment:
- "I'm interested, what's the next step?"
- "How do I get started?"
- "Sign me up"

### Test calculateROI:
- "How much money can I make?"
- "What's the ROI on this investment?"
- "I currently make $65,000 a year"

### Test qualifierNetworkAnalysis:
- "Tell me about becoming a qualifier"
- "How does the passive income work?"
- "Can I make $3,000 a month?"

### Test scheduleConsultation:
- "I need help with multi-state licensing"
- "I have a complex commercial situation"
- "I need expert advice"

## Webhook Implementation Status

All tools route to: `https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook`

✅ Implemented in webhook:
- searchKnowledge (fully functional with 469-entry database)
- detectPersona (persona detection logic)
- calculateTrust (trust scoring system)
- handleObjection (objection responses)

⚠️ Returns mock data (need full implementation):
- bookAppointment (returns confirmation)
- calculateROI (returns calculation)
- qualifierNetworkAnalysis (returns analysis)
- scheduleConsultation (returns booking)

## Tool IDs (For Reference)

- searchKnowledge: `511c7e72-ba2c-47cf-a0d9-fdbf3e91da09`
- detectPersona: `a3acffe3-fe06-4c86-9def-c10547a12890`
- calculateTrust: `59b97055-5d15-4bcb-938f-a7c6273ee8f9`
- handleObjection: `8110025e-9fa6-44b3-b27c-1d419f8699dd`
- bookAppointment: `26cf5647-28eb-4f66-b06f-7407a76f3779`
- calculateROI: `bd82fb63-448b-41b6-b98c-478123428776`
- qualifierNetworkAnalysis: `7a557d63-8bf5-4faf-950c-33c04747ab75`
- scheduleConsultation: `1435bf69-717a-4cf4-9757-5042a5d2da30`