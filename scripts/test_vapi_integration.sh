#!/bin/bash

echo "🚀 Testing VAPI Integration with Real Knowledge Base"
echo "===================================================================="

# Test the webhook endpoint directly
echo ""
echo "📡 Testing VAPI Webhook with searchKnowledge function:"
echo "--------------------------------------------------------------------"

curl -X POST https://hyper8-fact-fact-system.up.railway.app/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "function-call",
      "functionCall": {
        "name": "searchKnowledge",
        "parameters": {
          "query": "What are the requirements for a California contractor license?",
          "state": "CA"
        }
      }
    },
    "call": {
      "id": "test-call-123"
    }
  }' | python3 -m json.tool

echo ""
echo "===================================================================="
echo "✅ If you see real contractor licensing information above (not Georgia/exam/cost mock data),"
echo "   then the real knowledge base is connected!"
echo ""
echo "❌ If you got a 401 error, it means security is working but you need"
echo "   to add the webhook secret to test."
echo ""
echo "📝 Next steps:"
echo "1. Commit these changes"
echo "2. Push to repository"
echo "3. Deploy to Railway"
echo "4. Test VAPI calls to verify real data"