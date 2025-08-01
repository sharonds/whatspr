def fake_run_thread(thread_id, user_msg):
    """Mock agent that simulates the expected conversation flow"""
    if user_msg == "1":
        return "Great! Let's collect details for your funding round. What's the headline?", []
    else:
        return "Mock response to: " + user_msg, []
