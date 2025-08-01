# QA Test Plan - Press Release Intake Flow

## Overview
This test plan covers the press release intake flow functionality, ensuring the AI agent correctly collects all required information through a goal-oriented conversation.

## Test Environment
- Use staging environment with `.env.staging` configuration
- Assistant ID from `.assistant_id.staging`
- Flow: `pr_intake.yaml`

---

## Test Case 1: Announcement Type Collection

### Action (User Message)
"I want to create a press release"

### Expected Agent Response
- Agent should greet with the intro message containing "🚀 Great news!"
- Agent should ask about the type of announcement
- Response should include: "What type of announcement is this? (e.g., Funding, Product Launch)"

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "announcement_type", "value": "[user's response]"}
```

---

## Test Case 2: Headline Collection

### Action (User Message)
"This is a funding announcement"

### Expected Agent Response
- Agent should acknowledge the announcement type
- Agent should ask: "Do you have a headline in mind?"

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "announcement_type", "value": "funding announcement"}
```

---

## Test Case 3: Key Facts Collection

### Action (User Message)
"Tech Startup Raises $10M Series A"

### Expected Agent Response
- Agent should acknowledge the headline
- Agent should ask: "List the key facts: who, what, when, how much, investors."

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "headline", "value": "Tech Startup Raises $10M Series A"}
```

---

## Test Case 4: Quotes Collection

### Action (User Message)
"Company: TechCorp, Amount: $10M, Date: Today, Lead Investor: Venture Partners"

### Expected Agent Response
- Agent should acknowledge the key facts
- Agent should ask: "Provide two short quotes—one from the CEO and one from an investor."

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "key_facts", "value": "Company: TechCorp, Amount: $10M, Date: Today, Lead Investor: Venture Partners"}
```

---

## Test Case 5: Boilerplate Collection

### Action (User Message)
"CEO: 'We're thrilled about this funding.' Investor: 'TechCorp has amazing potential.'"

### Expected Agent Response
- Agent should acknowledge the quotes
- Agent should ask: "Share a one‑paragraph company boilerplate."

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "quotes", "value": "CEO: 'We're thrilled about this funding.' Investor: 'TechCorp has amazing potential.'"}
```

---

## Test Case 6: Media Contact Collection

### Action (User Message)
"TechCorp is a leading technology company focused on innovative solutions for businesses worldwide."

### Expected Agent Response
- Agent should acknowledge the boilerplate
- Agent should ask: "Who is the media contact (name, email, phone)?"

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "boilerplate", "value": "TechCorp is a leading technology company focused on innovative solutions for businesses worldwide."}
```

---

## Test Case 7: Flow Completion

### Action (User Message)
"John Doe, john@techcorp.com, 555-1234"

### Expected Agent Response
- Agent should acknowledge the media contact
- Agent should display the outro message: "✅ Got everything—expect your draft in 24 h. Reply /status anytime."
- Agent should indicate flow completion

### Log Verification
```
Tool call: save_slot
Arguments: {"name": "media_contact", "value": "John Doe, john@techcorp.com, 555-1234"}

Tool call: finish
Arguments: {}
```

---

## Test Case 8: Max Turns Limit

### Action (User Message)
Provide vague or incomplete responses for 12 turns

### Expected Agent Response
- After 12 turns, agent should complete the flow even if not all slots are filled
- Agent should gracefully handle incomplete data

### Log Verification
- Verify turn counter reaches 12
- Verify finish tool is called

---

## Test Case 9: Validation Testing

### Action (User Message)
Provide invalid data (e.g., email without @ symbol)

### Expected Agent Response
- Agent should use validation to detect invalid format
- Agent should ask for correction

### Log Verification
```
Tool call: validate_local
Arguments: {"name": "media_contact", "value": "[invalid email]"}
```

---

## Test Case 10: Context Retention

### Action (User Message)
1. "I want to create a press release"
2. "Actually, wait, what was the first question again?"

### Expected Agent Response
- Agent should maintain context
- Agent should repeat or clarify the current question

### Log Verification
```
Tool call: get_slot
Arguments: {"name": "[current_slot]"}
```

---

## Edge Cases

### Test Case 11: Empty Response Handling

### Action (User Message)
Send empty message or just spaces

### Expected Agent Response
- Agent should prompt user to provide information
- Agent should re-ask the current question

### Log Verification
- No save_slot call with empty value

---

### Test Case 12: Multiple Values in Single Response

### Action (User Message)
"Funding announcement. Headline: TechCorp Raises $10M. CEO John Smith."

### Expected Agent Response
- Agent should parse and save multiple slots if possible
- Agent should continue with next unfilled slot

### Log Verification
- Multiple save_slot calls in sequence

---

## Performance Criteria

1. **Response Time**: Agent should respond within 5 seconds
2. **Accuracy**: All slot values should be correctly captured
3. **Flow Completion**: Flow should complete within max_turns (12)
4. **Error Handling**: No crashes or unhandled exceptions
5. **Data Integrity**: All saved data should be retrievable

## Test Execution Notes

- Run each test case in isolation
- Clear thread/session between tests
- Monitor logs for tool calls
- Verify data persistence
- Test with both valid and invalid inputs
- Document any deviations from expected behavior