# VAPI Silent Transfer Squad - Deployment Steps

## Prerequisites

### 1. Environment Setup
```bash
# Ensure Python 3.8+ is installed
python3 --version

# Install required dependencies
pip install aiohttp python-dotenv

# Verify .env file has required keys
cat .env | grep VAPI_API_KEY
# Should show: VAPI_API_KEY=c49631b4-2f8f-40b3-9ce1-22f731879fb9
```

### 2. Verify FACT Webhook is Running
```bash
# Check Railway deployment status
curl https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health

# Expected response:
# {"status":"healthy","endpoint":"VAPI Webhook Handler","timestamp":"..."}
```

## Deployment Process

### Step 1: Clean Up Existing Resources (If Any)

#### 1.1 List Current Assistants
```bash
curl -X GET https://api.vapi.ai/assistant \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9" \
  -H "Content-Type: application/json" | python3 -m json.tool
```

#### 1.2 Delete Old Squad (If Exists)
```bash
# Replace SQUAD_ID with actual ID if different
curl -X DELETE https://api.vapi.ai/squad/[OLD_SQUAD_ID] \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9"
```

#### 1.3 Delete Old Assistants
```bash
# For each old assistant ID
curl -X DELETE https://api.vapi.ai/assistant/[ASSISTANT_ID] \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9"
```

### Step 2: Deploy Silent Transfer Squad

#### 2.1 Run Deployment Script
```bash
cd /Users/natperez/codebases/hyper8/hyper8-FACT
python scripts/create_silent_transfer_squad.py
```

**Expected Output:**
```
🚀 Creating VAPI Silent Transfer Squad
============================================================
✅ Created: CLP-Main-Router (ID: ...)
✅ Created: CLP-Veteran-Support (ID: ...)
✅ Created: CLP-Newcomer-Guide (ID: ...)
✅ Created: CLP-Fast-Track (ID: ...)
✅ Created: CLP-Network-Expert (ID: ...)
✅ Squad created: [SQUAD_ID]
```

#### 2.2 Verify Deployment
```bash
# Check configuration file was created
cat silent_transfer_squad_config.json | python3 -m json.tool
```

#### 2.3 Save Important IDs
```bash
# Extract key IDs from config
SQUAD_ID=$(cat silent_transfer_squad_config.json | python3 -c "import json,sys;print(json.load(sys.stdin).get('squad_id', 'Not found'))")
MAIN_ROUTER_ID=$(cat silent_transfer_squad_config.json | python3 -c "import json,sys;print(json.load(sys.stdin)['main_router_id'])")

echo "Squad ID: $SQUAD_ID"
echo "Main Router ID: $MAIN_ROUTER_ID"
```

### Step 3: Configure VAPI Dashboard

#### 3.1 Access VAPI Dashboard
1. Go to https://dashboard.vapi.ai
2. Navigate to Assistants section
3. Locate your newly created assistants

#### 3.2 Configure Phone Number (If Using)
1. Go to Phone Numbers section
2. Assign phone number to Main Router assistant
3. **Important:** Only assign to Main Router, not specialists

#### 3.3 Set Up Inbound Call Handler
```json
{
  "assistantId": "[MAIN_ROUTER_ID]",
  "squadId": "[SQUAD_ID]"
}
```

### Step 4: Test Silent Transfers

#### 4.1 Test via VAPI Dashboard
1. Click on Main Router assistant
2. Use "Test Call" feature
3. Follow test scenarios below

#### 4.2 Test Scenarios

**Scenario 1: Overwhelmed Veteran**
```
You: "This licensing process is so overwhelming, I don't know where to start"
Expected: Silent transfer to Veteran Support
Specialist: "I understand this feels overwhelming. Let's break this down step by step..."
```

**Scenario 2: Confused Newcomer**
```
You: "I'm completely new to contractor licensing"
Expected: Silent transfer to Newcomer Guide
Specialist: "Since you're new to this, let me explain the basics..."
```

**Scenario 3: Urgent Need**
```
You: "I need my license quickly, I have a job starting Friday"
Expected: Silent transfer to Fast Track
Specialist: "For your timeline, here's the expedited process..."
```

**Scenario 4: Business Opportunity**
```
You: "Can I make money helping others get licensed?"
Expected: Silent transfer to Network Expert
Specialist: "Regarding the business opportunity, the income potential..."
```

### Step 5: Verify Webhook Integration

#### 5.1 Test Knowledge Retrieval
```bash
# During a test call, ask:
"What are the requirements for a California contractor license?"

# Monitor webhook logs
curl https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health
```

#### 5.2 Check Railway Logs
```bash
# View recent webhook activity
railway logs --service fact-system --lines 50
```

### Step 6: Production Configuration

#### 6.1 Set Up Monitoring
```bash
# Create monitoring script
cat > monitor_squad.sh << 'EOF'
#!/bin/bash
SQUAD_ID="ca86111f-582f-4ba0-840f-e7a82dc0967d"
WEBHOOK_URL="https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health"

echo "Checking Squad Status..."
curl -s -X GET "https://api.vapi.ai/squad/$SQUAD_ID" \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9" \
  | python3 -m json.tool | head -20

echo -e "\nChecking Webhook Health..."
curl -s "$WEBHOOK_URL" | python3 -m json.tool
EOF

chmod +x monitor_squad.sh
```

#### 6.2 Configure Alerts (Optional)
```bash
# Set up webhook endpoint monitoring
# Use service like UptimeRobot or Pingdom to monitor:
# https://hyper8-fact-fact-system.up.railway.app/vapi/webhook/health
```

### Step 7: Documentation

#### 7.1 Document Configuration
```bash
# Create deployment record
cat > deployment_record.md << EOF
# VAPI Squad Deployment Record

**Date:** $(date)
**Squad ID:** $(cat silent_transfer_squad_config.json | python3 -c "import json,sys;print(json.load(sys.stdin).get('squad_id', 'Not set'))")
**Main Router:** $(cat silent_transfer_squad_config.json | python3 -c "import json,sys;print(json.load(sys.stdin)['main_router_id'])")
**Method:** Silent Transfer
**Webhook:** https://hyper8-fact-fact-system.up.railway.app/vapi/webhook

## Assistant IDs
$(cat silent_transfer_squad_config.json | python3 -m json.tool | grep -A 5 "assistant_ids")

## Notes
- All assistants use silent transfer method
- Main Router is the entry point for all calls
- Webhook secured with HMAC-SHA256
EOF
```

#### 7.2 Share with Team
```bash
# Export configuration for team
cp silent_transfer_squad_config.json squad_config_backup_$(date +%Y%m%d).json
cp VAPI_DEPLOYMENT_SUMMARY.md team_documentation/
```

## Rollback Procedure (If Needed)

### Quick Rollback
```bash
# 1. Delete new squad
curl -X DELETE https://api.vapi.ai/squad/[NEW_SQUAD_ID] \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9"

# 2. Delete new assistants
for id in $(cat silent_transfer_squad_config.json | python3 -c "import json,sys;d=json.load(sys.stdin);[print(v) for v in d['assistant_ids'].values()]"); do
  curl -X DELETE "https://api.vapi.ai/assistant/$id" \
    -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9"
done

# 3. Restore previous configuration (if backed up)
# python scripts/create_vapi_squad.py  # Old script
```

## Troubleshooting

### Issue: Transfers Not Working
```bash
# Check assistant names match exactly
curl -X GET https://api.vapi.ai/assistant/[MAIN_ROUTER_ID] \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9" \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print('Functions:', [f['name'] for f in d.get('functions', [])])"
```

### Issue: Webhook Not Responding
```bash
# Check Railway deployment
railway status

# Restart if needed
railway restart
```

### Issue: Wrong Assistant Answering
```bash
# Verify phone number assignment
# Should only be assigned to Main Router
curl -X GET https://api.vapi.ai/phone-number \
  -H "Authorization: Bearer c49631b4-2f8f-40b3-9ce1-22f731879fb9"
```

## Success Criteria

✅ **Deployment is successful when:**
1. All 5 assistants created successfully
2. Squad created with all members
3. Main Router receives test calls
4. Silent transfers execute without announcement
5. Specialists continue conversation naturally
6. Knowledge retrieval returns accurate information
7. No conversation interruptions occur

## Support Contacts

- **VAPI Support:** support@vapi.ai
- **Railway Support:** Via Railway dashboard
- **Internal Team:** Update with your team contacts

---

**Current Production Configuration:**
- Squad ID: `ca86111f-582f-4ba0-840f-e7a82dc0967d`
- Main Router: `686ead20-ceb5-45b3-a224-4ddb62f58bda`
- Status: DEPLOYED AND ACTIVE