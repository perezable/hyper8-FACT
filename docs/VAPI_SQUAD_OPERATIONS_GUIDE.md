# VAPI Squad Operations Guide

## Quick Reference Card

### Squad ID
```
860b548d-5199-4518-9a8e-7e0a665d3887
```

### Assistant Quick Reference
| Persona | Best For | Transfer When You Hear |
|---------|----------|------------------------|
| 🤝 **Veteran Support** | Overwhelmed, stressed callers | "Too much", "overwhelming", "can't handle" |
| 📚 **Newcomer Guide** | First-timers, confused callers | "New to this", "don't understand", "what is" |
| ⚡ **Fast Track** | Urgent, deadline-driven callers | "ASAP", "quickly", "deadline", "urgent" |
| 💼 **Network Expert** | Business-minded, opportunity seekers | "Make money", "business", "passive income" |

## How the System Works

### 1. Incoming Call Flow
```
Call arrives → Routes to first assistant (Veteran Support)
    ↓
Assistant greets caller
    ↓
System analyzes conversation
    ↓
If transfer needed → Assistant recommends specific specialist
    ↓
Operator executes manual transfer
```

### 2. When Assistants Recommend Transfers

The assistants will say things like:
- *"It sounds like you're working with a tight deadline. Let me connect you with our fast-track specialist..."*
- *"I can hear that this feels overwhelming. Let me connect you with our specialist who's great at breaking things down..."*
- *"I'm hearing interest in the business opportunities. Let me connect you with our network specialist..."*

**When you hear these, prepare to transfer the call.**

## Transfer Decision Guide

### From VETERAN SUPPORT Assistant

**Transfer to FAST TRACK when caller says:**
- "I need this quickly"
- "What's the fastest way"
- "I have a deadline"
- "This is urgent"

**Transfer to NETWORK EXPERT when caller says:**
- "Can I make money"
- "Business opportunity"
- "Help others get licensed"
- "Passive income"

**Transfer to NEWCOMER GUIDE when caller shows:**
- Confusion about basic terms
- Multiple "what does that mean" questions
- "I've never done this before"

### From NEWCOMER GUIDE Assistant

**Transfer to VETERAN SUPPORT when caller says:**
- "This is overwhelming"
- "It's too much"
- "I'm drowning in information"
- "I can't handle all this"

**Transfer to FAST TRACK when caller says:**
- "I need this by [date]"
- "How quickly can I get licensed"
- "This is time-sensitive"

**Transfer to NETWORK EXPERT when caller says:**
- "Tell me about the business side"
- "How can I make money"
- "Qualifier network sounds interesting"

### From FAST TRACK Assistant

**Transfer to VETERAN SUPPORT when caller says:**
- "The pressure is too much"
- "I'm stressed about the timeline"
- "This is overwhelming me"

**Transfer to NEWCOMER GUIDE when caller shows:**
- Doesn't understand basic licensing terms
- Asks multiple clarifying questions
- "Can you explain what that means"

**Transfer to NETWORK EXPERT when caller says:**
- "What about making money while getting licensed"
- "Tell me about the business opportunity"

### From NETWORK EXPERT Assistant

**Transfer to VETERAN SUPPORT when caller says:**
- "This business stuff is too complicated"
- "I'm overwhelmed by all the opportunities"
- "It's too much to think about"

**Transfer to FAST TRACK when caller says:**
- "I need to get licensed first, quickly"
- "Let's focus on the license for now"
- "What's the fastest path to licensing"

**Transfer to NEWCOMER GUIDE when caller says:**
- "I don't understand contractor licensing at all"
- "I'm completely new to this industry"
- "Can you explain the basics first"

## Behind the Scenes Functions

The system automatically:
1. **Searches Knowledge Base** - When callers ask questions
2. **Detects Personas** - Analyzes conversation patterns
3. **Tracks Trust** - Monitors engagement level
4. **Handles Objections** - Provides appropriate responses
5. **Gets State Requirements** - Retrieves location-specific info

## Trust Score Indicators

Watch for these assistant behaviors based on trust levels:

| Trust Level | Assistant Behavior | What It Means |
|-------------|-------------------|---------------|
| 🔴 **Low (0-49)** | Focus on rebuilding rapport | Caller is skeptical or disengaged |
| 🟡 **Medium (50-69)** | Building value, addressing concerns | Caller is interested but has questions |
| 🟢 **High (70-100)** | Moving toward commitment | Caller is ready to take action |

## Common Scenarios

### Scenario 1: The Overwhelmed Veteran
```
Caller: "I've been contracting for 20 years but this licensing stuff is killing me"
System: Detects overwhelmed_veteran persona
Action: Keep on Veteran Support Assistant (already matched)
```

### Scenario 2: The Rushed Newcomer
```
Caller: "I'm new to this and need my license by next Friday!"
System: Detects both confused_newcomer AND urgent_operator
Action: Transfer to Fast Track (urgency takes priority)
```

### Scenario 3: The Opportunity Seeker
```
Caller: "Can I really make money helping others get licensed?"
System: Detects qualifier_network_specialist
Action: Transfer to Network Expert
```

## Manual Transfer Process

### In VAPI Dashboard:
1. Click on active call
2. Select "Transfer" option
3. Choose target assistant from squad
4. Confirm warm transfer

### Transfer Best Practices:
- ✅ Wait for complete transfer recommendation from assistant
- ✅ Allow assistant to provide context before transferring
- ✅ Ensure smooth handoff with transfer message
- ❌ Don't transfer mid-sentence
- ❌ Don't transfer without assistant recommendation
- ❌ Don't transfer more than twice per call (indicates mismatch)

## Performance Monitoring

### Key Metrics to Track:
- **First Call Resolution:** Aim for 70%+
- **Average Transfers per Call:** Should be < 1.5
- **Transfer Success Rate:** Should be > 90%
- **Trust Score at Close:** Should be > 70

### Red Flags:
- Multiple transfers (3+) in single call
- Trust score dropping after transfer
- Caller asking for different specialist than recommended
- Repeated transfers between same two assistants

## Troubleshooting

### Issue: Assistant not recommending transfers
**Solution:** The persona detection may have low confidence. Listen for manual cues and use judgment.

### Issue: Multiple transfer recommendations
**Solution:** Prioritize based on urgency > confusion > business interest > overwhelm

### Issue: Caller refuses transfer
**Solution:** Current assistant can handle most queries; transfers are for optimization, not requirement

### Issue: System functions not working
**Solution:** Assistants have fallback responses and can continue conversation without webhook functions

## Emergency Procedures

### If Webhook is Down:
- Assistants continue with built-in knowledge
- Manual persona detection based on this guide
- Transfers still work but without smart recommendations

### If Squad is Unavailable:
- Fallback phone number: [Configure in VAPI]
- Manual routing based on initial questions
- Document incident for engineering team

## Contact & Support

### Technical Issues:
- Webhook URL: https://hyper8-fact-fact-system.up.railway.app/vapi/webhook
- Check Railway dashboard for system status

### Squad Configuration:
- Squad ID: 860b548d-5199-4518-9a8e-7e0a665d3887
- Access via VAPI Dashboard

### For Updates:
- Configuration file: `/vapi_squad_config.json`
- Documentation: `/docs/VAPI_SQUAD_FLOW_LOGIC.md`

---

Remember: The AI assistants are intelligent and will guide you. Trust their transfer recommendations, but use your judgment for edge cases.