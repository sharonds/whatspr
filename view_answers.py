#!/usr/bin/env python3
"""
View all stored WhatsApp conversation answers from the database.
"""

from sqlmodel import Session, select
from app.models import engine, SessionModel, Answer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def view_all_conversations():
    """Display all stored conversations and answers."""
    with Session(engine) as db:
        # Get all sessions
        sessions = db.exec(select(SessionModel)).all()

        if not sessions:
            print("No conversations found in database.")
            return

        for session in sessions:
            print(f"\n📱 Session ID: {session.id}")
            print(f"📞 Phone: {session.phone}")
            print(f"✅ Completed: {session.completed}")
            print(f"🕐 Created: {session.created_at}")

            # Get all answers for this session
            answers = db.exec(select(Answer).where(Answer.session_id == session.id)).all()

            if answers:
                print(f"\n💬 Answers ({len(answers)} total):")
                for answer in answers:
                    print(f"  {answer.field}: {answer.value}")
            else:
                print("  No answers yet.")

            print("-" * 50)


if __name__ == "__main__":
    view_all_conversations()
