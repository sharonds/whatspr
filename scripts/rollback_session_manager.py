#!/usr/bin/env python3
"""Session Manager Rollback Script.

Emergency rollback script to disable SessionManager and migrate back to
legacy dictionary-based session storage. Use if SessionManager causes
issues during MVP deployment with real users.

Usage:
    python scripts/rollback_session_manager.py [--dry-run] [--backup]
    
Options:
    --dry-run    Show what would be done without making changes
    --backup     Create backup of current session data before rollback
"""

import sys
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from session_manager import SessionManager
from session_config.session_config import SessionConfig


def create_backup(session_manager: SessionManager, backup_dir: Path) -> Path:
    """Create backup of current session data.
    
    Args:
        session_manager: The SessionManager instance to backup.
        backup_dir: Directory to store backup files.
        
    Returns:
        Path: Path to the created backup file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"session_backup_{timestamp}.json"
    
    # Extract session data
    backup_data = {
        "timestamp": timestamp,
        "sessions": {},
        "metrics": session_manager.get_metrics(),
        "config": {
            "ttl_seconds": session_manager.config.ttl_seconds,
            "cleanup_interval": session_manager.config.cleanup_interval
        }
    }
    
    # Convert sessions to serializable format
    for phone, entry in session_manager._sessions.items():
        backup_data["sessions"][phone] = {
            "thread_id": entry.thread_id,
            "created_at": entry.created_at.isoformat(),
            "last_accessed": entry.last_accessed.isoformat()
        }
    
    # Ensure backup directory exists
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Write backup file
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Session backup created: {backup_file}")
    print(f"   Sessions backed up: {len(backup_data['sessions'])}")
    print(f"   Active sessions: {backup_data['metrics']['active_sessions']}")
    
    return backup_file


def migrate_to_legacy_format(session_manager: SessionManager) -> Dict[str, Optional[str]]:
    """Convert SessionManager data to legacy dictionary format.
    
    Args:
        session_manager: The SessionManager to convert.
        
    Returns:
        Dict[str, Optional[str]]: Legacy format dictionary (phone -> thread_id).
    """
    legacy_sessions = {}
    
    for phone, entry in session_manager._sessions.items():
        # Only include active sessions (non-expired)
        if not session_manager._is_expired(entry):
            legacy_sessions[phone] = entry.thread_id
        else:
            # Include expired sessions as None to preserve phone numbers
            legacy_sessions[phone] = None
    
    return legacy_sessions


def modify_agent_endpoint(dry_run: bool = False) -> bool:
    """Modify agent_endpoint.py to disable SessionManager.
    
    Args:
        dry_run: If True, only show what would be changed.
        
    Returns:
        bool: True if modification was successful (or would be in dry-run).
    """
    agent_endpoint_path = Path(__file__).parent.parent / "app" / "agent_endpoint.py"
    
    if not agent_endpoint_path.exists():
        print(f"❌ Error: {agent_endpoint_path} not found")
        return False
    
    # Read current file
    with open(agent_endpoint_path, 'r') as f:
        content = f.read()
    
    # Check current state
    if "USE_SESSION_MANAGER = False" in content:
        print("ℹ️  SessionManager already disabled in agent_endpoint.py")
        return True
    
    if "USE_SESSION_MANAGER = True" not in content:
        print("⚠️  Warning: USE_SESSION_MANAGER flag not found in expected format")
        print("   Manual intervention may be required")
        return False
    
    if dry_run:
        print("🔍 DRY RUN: Would change USE_SESSION_MANAGER = True to False")
        return True
    
    # Create backup of original file
    backup_path = agent_endpoint_path.with_suffix('.py.backup')
    shutil.copy2(agent_endpoint_path, backup_path)
    print(f"📁 Created backup: {backup_path}")
    
    # Make the change
    new_content = content.replace(
        "USE_SESSION_MANAGER = True",
        "USE_SESSION_MANAGER = False  # ROLLED BACK - was True"
    )
    
    # Write modified file
    with open(agent_endpoint_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Modified agent_endpoint.py to disable SessionManager")
    return True


def create_migration_data_file(legacy_sessions: Dict[str, Optional[str]], 
                              backup_file: Path, 
                              dry_run: bool = False) -> Optional[Path]:
    """Create migration data file for emergency restoration.
    
    Args:
        legacy_sessions: The legacy format session data.
        backup_file: Path to the backup file.
        dry_run: If True, only show what would be created.
        
    Returns:
        Optional[Path]: Path to migration file, or None if dry-run.
    """
    if dry_run:
        print("🔍 DRY RUN: Would create migration data file with:")
        print(f"   Legacy sessions: {len(legacy_sessions)}")
        print(f"   Active sessions: {len([v for v in legacy_sessions.values() if v])}")
        return None
    
    migration_file = Path(__file__).parent.parent / "session_migration_data.json"
    
    migration_data = {
        "rollback_timestamp": datetime.now().isoformat(),
        "backup_file": str(backup_file),
        "legacy_sessions": legacy_sessions,
        "rollback_reason": "Emergency rollback from SessionManager to legacy dict",
        "restoration_command": "python scripts/restore_session_manager.py"
    }
    
    with open(migration_file, 'w') as f:
        json.dump(migration_data, f, indent=2)
    
    print(f"📄 Created migration data file: {migration_file}")
    return migration_file


def rollback_session_manager(dry_run: bool = False, create_backup_flag: bool = True):
    """Main rollback function.
    
    Args:
        dry_run: If True, show what would be done without making changes.
        create_backup_flag: If True, create backup before rollback.
    """
    print("🚨 Session Manager Emergency Rollback")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    # Initialize session manager to get current state
    try:
        session_manager = SessionManager(SessionConfig())
        current_metrics = session_manager.get_metrics()
        
        print(f"📊 Current SessionManager Status:")
        print(f"   Active sessions: {current_metrics['active_sessions']}")
        print(f"   Total created: {current_metrics['total_sessions_created']}")
        print(f"   Memory usage: {current_metrics['estimated_memory_bytes']} bytes")
        print()
        
    except Exception as e:
        print(f"❌ Error initializing SessionManager: {e}")
        print("   Proceeding with code-only rollback...")
        session_manager = None
    
    # Step 1: Create backup if requested and possible
    backup_file = None
    if create_backup_flag and session_manager and not dry_run:
        try:
            backup_dir = Path(__file__).parent.parent / "backups"
            backup_file = create_backup(session_manager, backup_dir)
        except Exception as e:
            print(f"⚠️  Warning: Backup creation failed: {e}")
            print("   Continuing with rollback...")
    
    # Step 2: Convert to legacy format
    legacy_sessions = {}
    if session_manager:
        try:
            legacy_sessions = migrate_to_legacy_format(session_manager)
            print(f"🔄 Converted to legacy format:")
            print(f"   Total entries: {len(legacy_sessions)}")
            print(f"   Active sessions: {len([v for v in legacy_sessions.values() if v])}")
            print()
        except Exception as e:
            print(f"⚠️  Warning: Session migration failed: {e}")
            print("   Legacy sessions will start empty after rollback")
    
    # Step 3: Modify agent_endpoint.py
    if not modify_agent_endpoint(dry_run):
        print("❌ Failed to modify agent_endpoint.py")
        return False
    
    # Step 4: Create migration data file for future restoration
    if backup_file:
        migration_file = create_migration_data_file(legacy_sessions, backup_file, dry_run)
    
    print("\n✅ Rollback Complete!")
    print("📋 Summary:")
    print("   - SessionManager disabled in agent_endpoint.py")
    print("   - Legacy dictionary-based sessions will be used")
    if backup_file:
        print(f"   - Session data backed up to: {backup_file}")
    print("   - Application restart required to take effect")
    
    print("\n🔄 Next Steps:")
    print("1. Restart your application (uvicorn/gunicorn)")
    print("2. Monitor /health/sessions endpoint to confirm legacy mode")
    print("3. Check application logs for any issues")
    
    if backup_file:
        print("4. To restore SessionManager later: python scripts/restore_session_manager.py")
    
    return True


def main():
    """Main script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Emergency Session Manager rollback")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--backup", action="store_true", default=True,
                       help="Create backup before rollback (default: True)")
    parser.add_argument("--no-backup", action="store_true", 
                       help="Skip backup creation")
    
    args = parser.parse_args()
    
    # Handle backup flags
    create_backup_flag = args.backup and not args.no_backup
    
    if args.dry_run:
        print("Running in DRY RUN mode - no changes will be made")
    
    if not create_backup_flag:
        print("⚠️  WARNING: Running without backup creation")
        if not args.dry_run:
            confirm = input("Continue without backup? (y/N): ")
            if confirm.lower() != 'y':
                print("Rollback cancelled")
                return
    
    success = rollback_session_manager(
        dry_run=args.dry_run, 
        create_backup_flag=create_backup_flag
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()