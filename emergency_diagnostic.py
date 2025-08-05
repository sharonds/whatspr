#!/usr/bin/env python3
"""
Emergency WhatsApp Diagnostic Script
Comprehensive testing to identify the exact failure point
"""

import requests
import subprocess
from datetime import datetime


def test_local_server():
    """Test if local server responds"""
    print("🏥 Testing Local Server")
    print("-" * 30)

    try:
        response = requests.post(
            "http://localhost:8004/agent",
            data={"From": "whatsapp:+31621366440", "Body": "We are going to the moon"},
            timeout=30,
        )

        print(f"✅ Local server: {response.status_code}")
        print(f"📝 Response: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Local server failed: {e}")
        return False


def test_ngrok_tunnel():
    """Test ngrok tunnel status"""
    print("\n🌐 Testing Ngrok Tunnel")
    print("-" * 30)

    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        data = response.json()

        for tunnel in data.get('tunnels', []):
            if tunnel['proto'] == 'https':
                url = tunnel['public_url']
                print(f"✅ Found tunnel: {url}")

                # Test the tunnel
                test_response = requests.post(
                    f"{url}/agent",
                    data={"From": "whatsapp:+31621366440", "Body": "We are going to the moon"},
                    timeout=30,
                )

                print(f"📡 Tunnel test: {test_response.status_code}")
                print(f"📝 Response: {test_response.text[:100]}...")
                return url

    except Exception as e:
        print(f"❌ Ngrok tunnel failed: {e}")
        return None


def test_specific_url():
    """Test the specific URL WhatsApp is using"""
    print("\n📱 Testing WhatsApp's URL")
    print("-" * 30)

    url = "https://ce076506d1fa.ngrok.app/agent"

    try:
        response = requests.post(
            url,
            data={"From": "whatsapp:+31621366440", "Body": "We are going to the moon"},
            timeout=30,
        )

        print(f"✅ WhatsApp URL: {response.status_code}")
        print(f"📝 Response: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ WhatsApp URL failed: {e}")
        return False


def check_server_logs():
    """Check recent server logs"""
    print("\n📋 Recent Server Logs")
    print("-" * 30)

    try:
        result = subprocess.run(
            ['tail', '-20', 'server_diagnostic.log'], capture_output=True, text=True, timeout=5
        )

        lines = result.stdout.split('\n')
        recent_lines = [line for line in lines if line.strip()][-5:]

        for line in recent_lines:
            print(f"📄 {line}")

    except Exception as e:
        print(f"❌ Log check failed: {e}")


def check_assistant_config():
    """Check which assistant is being used"""
    print("\n🤖 Assistant Configuration")
    print("-" * 30)

    # Check cached assistant ID
    try:
        with open('.assistant_id', 'r') as f:
            cached_id = f.read().strip()
        print(f"📋 Cached assistant: {cached_id}")
    except:
        print("❌ No .assistant_id file")

    try:
        with open('.assistant_id.staging', 'r') as f:
            staging_id = f.read().strip()
        print(f"📋 Staging assistant: {staging_id}")
    except:
        print("❌ No .assistant_id.staging file")

    print("📋 update_assistant.py targets: asst_5MmNyeVDUeYi3RnbX0jCuSpU")


def main():
    print("🚨 EMERGENCY WHATSAPP DIAGNOSTIC")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()

    # Test 1: Local server
    local_ok = test_local_server()

    # Test 2: Ngrok tunnel
    tunnel_url = test_ngrok_tunnel()

    # Test 3: Specific WhatsApp URL
    whatsapp_ok = test_specific_url()

    # Test 4: Server logs
    check_server_logs()

    # Test 5: Assistant config
    check_assistant_config()

    # Summary
    print("\n🎯 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"Local Server: {'✅ OK' if local_ok else '❌ FAILED'}")
    print(f"Ngrok Tunnel: {'✅ OK' if tunnel_url else '❌ FAILED'}")
    print(f"WhatsApp URL: {'✅ OK' if whatsapp_ok else '❌ FAILED'}")

    if local_ok and not whatsapp_ok:
        print("\n💡 DIAGNOSIS: Server works locally but ngrok tunnel is broken")
        print("   SOLUTION: Restart ngrok and update Twilio webhook URL")
    elif not local_ok:
        print("\n💡 DIAGNOSIS: Local server is not responding")
        print("   SOLUTION: Check server process and restart if needed")
    else:
        print("\n💡 All tests passed - investigate other causes")


if __name__ == "__main__":
    main()
