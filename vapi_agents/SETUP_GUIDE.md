# VAPI Agent Setup Guide

## How to Import the Agents into VAPI

### Option 1: Manual Import via VAPI Dashboard

1. **Login to VAPI Dashboard**
   - Go to https://dashboard.vapi.ai
   - Navigate to "Assistants" section

2. **Create Inbound Sales Agent**
   - Click "Create Assistant"
   - Name: "CLP Sales Specialist"
   - Copy the configuration from `inbound_sales_agent.json`
   - Set the webhook URL to: `https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook`
   - Save the assistant and note the Assistant ID

3. **Create Expert Agent**
   - Click "Create Assistant" again
   - Name: "CLP Expert Consultant"
   - Copy the configuration from `inbound_expert_agent.json`
   - Set the webhook URL to: `https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook`
   - Save the assistant and note the Assistant ID

4. **Link the Agents for Transfers**
   - Edit the Sales Agent
   - Add the Expert Agent's Assistant ID to the transfer list
   - Save changes

### Option 2: Use VAPI API

Run the setup script below with your VAPI API key:

```bash
# Set your VAPI API key
export VAPI_API_KEY="your-api-key-here"

# Run the setup script
python vapi_agents/setup_agents.py
```

## Required VAPI Account Settings

1. **API Key**: Get from https://dashboard.vapi.ai/api-keys
2. **Phone Number**: Purchase a phone number in VAPI for inbound calls
3. **Webhook Secret**: Set in your Railway environment variables

## Testing the Agents

1. **Assign Phone Number**
   - In VAPI Dashboard, go to "Phone Numbers"
   - Assign your number to the "CLP Sales Specialist" assistant

2. **Test Call Flow**
   - Call your VAPI phone number
   - Test various personas:
     - Say "I'm overwhelmed by all this paperwork" (Overwhelmed Veteran)
     - Say "I'm new to contracting" (Confused Newcomer)
     - Say "I need this quickly" (Urgent Operator)
     - Say "Tell me about the income opportunities" (Strategic Investor)

3. **Test Transfer**
   - Build trust by showing interest
   - Ask about "qualifier network" or "passive income"
   - Agent should offer to transfer to expert

## Environment Variables Needed

Add these to your Railway deployment:

```env
VAPI_WEBHOOK_SECRET=your-webhook-secret
DATABASE_URL=your-postgres-url
ANTHROPIC_API_KEY=your-anthropic-key
```

## Monitoring

View conversation summaries at:
```
GET https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/conversation/{call_id}/summary
```

## Troubleshooting

- **Agents not responding**: Check webhook URL is correct
- **No knowledge base answers**: Verify PostgreSQL has data (469 entries)
- **Transfer not working**: Ensure both agent IDs are correctly linked
- **Voice issues**: Verify ElevenLabs integration in VAPI account