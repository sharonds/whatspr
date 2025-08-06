#!/usr/bin/env python3
"""
Simple test script for menu conversation flow.
Tests our numeric menu preprocessing without complex mocking.
"""

import requests


def test_menu_conversation():
    """Test the numeric menu selection conversation flow."""
    base_url = "http://localhost:8004/agent"
    phone = "whatsapp:+15551234567"

    print("🧪 Testing Menu Conversation Flow")
    print("=" * 50)

    def send_message(body, description):
        print(f"\n📤 {description}")
        print(f"Sending: '{body}'")

        response = requests.post(
            base_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"From={phone}&Body={body}",
            timeout=30,
        )

        if response.status_code == 200:
            # Extract message from TwiML
            text = response.text
            if "<Message>" in text:
                message = text.split("<Message>")[1].split("</Message>")[0]
                print(f"📥 Response: {message}")
                return message
            else:
                print(f"📥 Raw response: {text}")
                return text
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None

    try:
        # Test 1: Reset conversation
        reset_response = send_message("reset", "Reset conversation")
        assert reset_response is not None
        assert "Press 1 for" in reset_response

        # Test 2: Select option 1 (Funding round)
        option1_response = send_message("1", "Select option 1 (Funding round)")
        assert option1_response is not None
        assert "oops" not in option1_response.lower()
        print("✅ Option 1 processed successfully")

        # Test 3: Provide company name
        company_response = send_message("TechCorp Inc", "Provide company name")
        assert company_response is not None
        assert "oops" not in company_response.lower()
        print("✅ Company name processed successfully")

        # Test 4: Provide funding amount
        funding_response = send_message("$15 million", "Provide funding amount")
        assert funding_response is not None
        assert "oops" not in funding_response.lower()
        print("✅ Funding amount processed successfully")

        # Test 5: Test another menu option
        reset_response2 = send_message("reset", "Reset for second test")
        assert reset_response2 is not None
        assert "Press 2 for" in reset_response2

        option2_response = send_message("2", "Select option 2 (Product launch)")
        assert option2_response is not None
        assert "oops" not in option2_response.lower()
        print("✅ Option 2 processed successfully")

        # Test 6: Test third menu option
        reset_response3 = send_message("reset", "Reset for third test")
        assert reset_response3 is not None
        assert "Press 3 for" in reset_response3

        option3_response = send_message("3", "Select option 3 (Partnership)")
        assert option3_response is not None
        assert "oops" not in option3_response.lower()
        print("✅ Option 3 processed successfully")

        print("\n🎉 All menu conversation tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_menu_conversation()
    exit(0 if success else 1)
