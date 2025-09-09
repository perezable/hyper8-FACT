/**
 * VAPI Integration Example for FACT Knowledge Base
 * 
 * This example shows how to integrate VAPI with FACT for
 * intelligent contractor licensing voice agents.
 */

const axios = require('axios');

// Configuration
const VAPI_API_KEY = process.env.VAPI_API_KEY;
const FACT_API_URL = 'https://hyper8-fact-fact-system.up.railway.app';
const VAPI_BASE_URL = 'https://api.vapi.ai';

/**
 * Create a VAPI assistant with FACT integration
 */
async function createVAPIAssistant() {
  const assistantConfig = {
    name: "CLP Licensing Expert",
    firstMessage: "Hi! I'm here to help you get your contractor's license. What state are you interested in?",
    model: {
      provider: "openai",
      model: "gpt-4-turbo",
      temperature: 0.7,
      systemPrompt: `You are an expert contractor licensing advisor. 
        Use these functions to provide accurate information:
        - searchKnowledge: For any licensing questions
        - detectPersona: At the start of conversations
        - calculateTrust: Throughout the conversation
        - getStateRequirements: For state-specific info
        - handleObjection: When caller has concerns
        
        Keep responses concise and conversational for voice interaction.`
    },
    voice: {
      provider: "elevenlabs",
      voiceId: "21m00Tcm4TlvDq8ikWAM"
    },
    functions: [
      {
        name: "searchKnowledge",
        description: "Search contractor licensing knowledge base",
        parameters: {
          type: "object",
          properties: {
            query: { type: "string" },
            state: { type: "string" },
            category: { type: "string" }
          },
          required: ["query"]
        },
        serverUrl: `${FACT_API_URL}/vapi/webhook`
      },
      {
        name: "detectPersona",
        description: "Detect caller persona for conversation adjustment",
        parameters: {
          type: "object",
          properties: {
            text: { type: "string" }
          },
          required: ["text"]
        },
        serverUrl: `${FACT_API_URL}/vapi/webhook`
      },
      {
        name: "calculateTrust",
        description: "Track trust score throughout conversation",
        parameters: {
          type: "object",
          properties: {
            events: { 
              type: "array",
              items: {
                type: "object",
                properties: {
                  type: { type: "string" },
                  description: { type: "string" }
                }
              }
            }
          },
          required: ["events"]
        },
        serverUrl: `${FACT_API_URL}/vapi/webhook`
      },
      {
        name: "getStateRequirements",
        description: "Get specific state licensing requirements",
        parameters: {
          type: "object",
          properties: {
            state: { type: "string" }
          },
          required: ["state"]
        },
        serverUrl: `${FACT_API_URL}/vapi/webhook`
      },
      {
        name: "handleObjection",
        description: "Get response for caller objections",
        parameters: {
          type: "object",
          properties: {
            type: { 
              type: "string",
              enum: ["too_expensive", "need_time", "not_sure", "too_complicated"]
            }
          },
          required: ["type"]
        },
        serverUrl: `${FACT_API_URL}/vapi/webhook`
      }
    ]
  };

  try {
    const response = await axios.post(
      `${VAPI_BASE_URL}/assistant`,
      assistantConfig,
      {
        headers: {
          'Authorization': `Bearer ${VAPI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Assistant created:', response.data.id);
    return response.data;
  } catch (error) {
    console.error('Error creating assistant:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Create a VAPI squad with persona-based routing
 */
async function createVAPISquad() {
  const squadConfig = {
    name: "CLP Expert Squad",
    members: [
      {
        assistantId: "asst_xxx_veteran", // Replace with actual assistant ID
        transferCondition: {
          operator: "equals",
          left: "{{persona}}",
          right: "overwhelmed_veteran"
        }
      },
      {
        assistantId: "asst_xxx_newcomer", // Replace with actual assistant ID
        transferCondition: {
          operator: "equals",
          left: "{{persona}}",
          right: "confused_newcomer"
        }
      },
      {
        assistantId: "asst_xxx_general", // Replace with actual assistant ID
        transferCondition: {
          operator: "default",
          left: "true",
          right: "true"
        }
      }
    ],
    transferMode: "warm"
  };

  try {
    const response = await axios.post(
      `${VAPI_BASE_URL}/squad`,
      squadConfig,
      {
        headers: {
          'Authorization': `Bearer ${VAPI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Squad created:', response.data.id);
    return response.data;
  } catch (error) {
    console.error('Error creating squad:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Make an outbound call using VAPI
 */
async function makeOutboundCall(phoneNumber, assistantId) {
  const callConfig = {
    assistantId: assistantId,
    customer: {
      number: phoneNumber
    },
    phoneNumberId: "your_phone_number_id" // Replace with your VAPI phone number ID
  };

  try {
    const response = await axios.post(
      `${VAPI_BASE_URL}/call`,
      callConfig,
      {
        headers: {
          'Authorization': `Bearer ${VAPI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Call initiated:', response.data.id);
    return response.data;
  } catch (error) {
    console.error('Error making call:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Test FACT webhook directly
 */
async function testFACTWebhook() {
  const testRequest = {
    message: {
      type: "function-call",
      functionCall: {
        name: "searchKnowledge",
        parameters: {
          query: "Georgia contractor license requirements",
          state: "GA"
        }
      }
    },
    call: {
      id: "test_call_123",
      assistantId: "test_assistant"
    }
  };

  try {
    const response = await axios.post(
      `${FACT_API_URL}/vapi/webhook`,
      testRequest,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('FACT Response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error) {
    console.error('Error testing FACT webhook:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Monitor call analytics
 */
async function getCallAnalytics(callId) {
  try {
    const response = await axios.get(
      `${FACT_API_URL}/api/v1/knowledge/analytics/conversation/${callId}`,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Call Analytics:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error) {
    console.error('Error getting analytics:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Example workflow
 */
async function runExample() {
  console.log('🚀 VAPI + FACT Integration Example\n');
  
  // Test FACT webhook
  console.log('1. Testing FACT webhook...');
  await testFACTWebhook();
  
  // Create assistant (uncomment with valid API key)
  // console.log('\n2. Creating VAPI assistant...');
  // const assistant = await createVAPIAssistant();
  
  // Create squad (uncomment with valid API key and assistant IDs)
  // console.log('\n3. Creating VAPI squad...');
  // const squad = await createVAPISquad();
  
  // Make test call (uncomment with valid configuration)
  // console.log('\n4. Making outbound call...');
  // const call = await makeOutboundCall('+1234567890', assistant.id);
  
  // Get analytics (after call completes)
  // console.log('\n5. Getting call analytics...');
  // setTimeout(async () => {
  //   await getCallAnalytics(call.id);
  // }, 60000); // Check after 1 minute
  
  console.log('\n✅ Example completed!');
}

// Run the example
if (require.main === module) {
  runExample().catch(console.error);
}

module.exports = {
  createVAPIAssistant,
  createVAPISquad,
  makeOutboundCall,
  testFACTWebhook,
  getCallAnalytics
};