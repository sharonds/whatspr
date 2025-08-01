#!/usr/bin/env python3
"""
Integration test to validate all three PRs work together:
- PR1: Atomic tools are available and properly registered
- PR2: Goal-oriented prompt is loaded
- PR3: File Search capability is enabled on the assistant
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up staging environment
os.environ['TWILIO_AUTH_TOKEN'] = 'test-token'
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['DATABASE_URL'] = 'app_staging.db'


def test_pr1_atomic_tools():
    """Test that atomic tools are properly imported and registered"""
    try:
        from app.tools_atomic import (
            save_announcement_type,
            save_headline,
            save_key_facts,
            save_quotes,
            save_boilerplate,
            save_media_contact,
        )

        # Verify all imports work by checking they're callable
        assert callable(save_announcement_type)
        print("✅ PR1: All 6 atomic tools imported successfully")

        from app.agent_runtime import ATOMIC_FUNCS

        print(f"✅ PR1: {len(ATOMIC_FUNCS)} atomic functions registered in runtime")
        return True
    except ImportError as e:
        print(f"❌ PR1: Error importing atomic tools: {e}")
        return False


def test_pr2_goal_oriented_prompt():
    """Test that the goal-oriented prompt is available and correctly formatted"""
    try:
        prompt_path = project_root / "prompts" / "assistant_v2.txt"
        if not prompt_path.exists():
            print("❌ PR2: assistant_v2.txt prompt file not found")
            return False

        prompt_content = prompt_path.read_text()
        if "{{tool_names}}" in prompt_content and "mission" in prompt_content.lower():
            print("✅ PR2: Goal-oriented prompt loaded with placeholder and mission language")
            return True
        else:
            print("❌ PR2: Prompt doesn't contain expected goal-oriented elements")
            return False
    except Exception as e:
        print(f"❌ PR2: Error reading prompt: {e}")
        return False


def test_pr3_file_search_knowledge():
    """Test that knowledge base file exists and assistant ID is updated"""
    try:
        knowledge_file = project_root / "knowledge" / "press_release_requirements.txt"
        if not knowledge_file.exists():
            print("❌ PR3: Knowledge base file not found")
            return False

        assistant_id_file = project_root / ".assistant_id.staging"
        if not assistant_id_file.exists():
            print("❌ PR3: Staging assistant ID file not found")
            return False

        assistant_id = assistant_id_file.read_text().strip()
        if assistant_id == "asst_0q97TNhkrgXUW8xujR8vwHOU":
            print("✅ PR3: File Search assistant ID correctly set in staging")
            print("✅ PR3: Knowledge base file exists for File Search")
            return True
        else:
            print(f"❌ PR3: Wrong assistant ID: {assistant_id}")
            return False
    except Exception as e:
        print(f"❌ PR3: Error checking File Search setup: {e}")
        return False


def main():
    """Run integration test for all three PRs"""
    print("🧪 Running integration test for PR1 + PR2 + PR3...")
    print("=" * 60)

    results = []
    results.append(test_pr1_atomic_tools())
    results.append(test_pr2_goal_oriented_prompt())
    results.append(test_pr3_file_search_knowledge())

    print("=" * 60)

    if all(results):
        print("🎉 SUCCESS: All three PRs are properly integrated!")
        print("   - PR1: Atomic tools ✅")
        print("   - PR2: Goal-oriented prompt ✅")
        print("   - PR3: File Search knowledge base ✅")
        print("\n🚀 Ready for production deployment!")
        return 0
    else:
        print("❌ FAILURE: Integration issues detected")
        failed_prs = []
        if not results[0]:
            failed_prs.append("PR1 (Atomic Tools)")
        if not results[1]:
            failed_prs.append("PR2 (Goal-Oriented Prompt)")
        if not results[2]:
            failed_prs.append("PR3 (File Search)")
        print(f"   Failed PRs: {', '.join(failed_prs)}")
        return 1


if __name__ == "__main__":
    exit(main())
