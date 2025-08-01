def fake_run_thread(thread_id, user_msg):
    """Mock agent that simulates the expected conversation flow"""
    # Debug print to help with CI debugging
    print(f"[MOCK] Called with: thread_id={thread_id[:8]}..., user_msg='{user_msg}'")
    
    if user_msg == "1":
        response = "Great! Let's collect details for your funding round. What's the headline?"
        print(f"[MOCK] Returning: '{response[:50]}...'")
        return response, []
    else:
        response = "Mock response to: " + user_msg
        print(f"[MOCK] Returning: '{response}'")
        return response, []
