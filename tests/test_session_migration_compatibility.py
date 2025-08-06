"""Session Migration Compatibility Testing.

Tests backward compatibility with existing session migration functionality
and ensures smooth transition from legacy dictionary-based sessions.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.session_manager import SessionManager, SessionEntry
from app.session_config.session_config import SessionConfig
from tests.utils.rate_limiter import RateLimitedTestCase


class TestSessionMigrationCompatibility(RateLimitedTestCase):
    """Test backward compatibility with existing session migration."""

    def setUp(self):
        """Set up test with clean session manager."""
        self.test_config = SessionConfig(
            ttl_seconds=3600,  # 1 hour for realistic testing
            cleanup_interval=300,  # 5 minutes
        )
        self.session_manager = SessionManager(self.test_config)

    def test_migrate_from_empty_dict(self):
        """Test migration from empty legacy sessions dictionary."""
        empty_sessions = {}
        
        migrated_count = self.session_manager.migrate_from_dict(empty_sessions)
        
        assert migrated_count == 0
        assert len(self.session_manager._sessions) == 0
        
        metrics = self.session_manager.get_metrics()
        assert metrics['active_sessions'] == 0
        assert metrics['total_sessions_created'] == 0

    def test_migrate_from_valid_sessions(self):
        """Test migration from valid legacy sessions dictionary."""
        legacy_sessions = {
            "+1234567890": "thread_abc123",
            "+1987654321": "thread_def456",
            "+1555555555": "thread_ghi789"
        }
        
        migrated_count = self.session_manager.migrate_from_dict(legacy_sessions)
        
        assert migrated_count == 3
        assert len(self.session_manager._sessions) == 3
        
        # Verify all sessions accessible
        assert self.session_manager.get_session("+1234567890") == "thread_abc123"
        assert self.session_manager.get_session("+1987654321") == "thread_def456"
        assert self.session_manager.get_session("+1555555555") == "thread_ghi789"
        
        # Verify metrics updated
        metrics = self.session_manager.get_metrics()
        assert metrics['active_sessions'] == 3
        assert metrics['total_sessions_created'] == 3

    def test_migrate_with_invalid_entries(self):
        """Test migration skips invalid entries correctly."""
        mixed_sessions = {
            "+1234567890": "thread_valid_1",
            "+1987654321": None,  # Should be skipped
            "+1555555555": "",    # Should be skipped
            "+1111111111": "   ", # Should be skipped (whitespace only)
            "+1222222222": "thread_valid_2"
        }
        
        migrated_count = self.session_manager.migrate_from_dict(mixed_sessions)
        
        assert migrated_count == 2  # Only valid entries
        assert len(self.session_manager._sessions) == 2
        
        # Verify only valid sessions exist
        assert self.session_manager.get_session("+1234567890") == "thread_valid_1"
        assert self.session_manager.get_session("+1222222222") == "thread_valid_2"
        
        # Verify invalid entries skipped
        assert self.session_manager.get_session("+1987654321") is None
        assert self.session_manager.get_session("+1555555555") is None
        assert self.session_manager.get_session("+1111111111") is None

    def test_migrate_preserves_existing_sessions(self):
        """Test migration preserves existing sessions in SessionManager."""
        # Create existing session
        self.session_manager.set_session("+1000000000", "thread_existing")
        
        # Migrate from legacy dict
        legacy_sessions = {
            "+1234567890": "thread_migrated_1",
            "+1987654321": "thread_migrated_2"
        }
        
        initial_metrics = self.session_manager.get_metrics()
        migrated_count = self.session_manager.migrate_from_dict(legacy_sessions)
        final_metrics = self.session_manager.get_metrics()
        
        assert migrated_count == 2
        assert len(self.session_manager._sessions) == 3  # 1 existing + 2 migrated
        
        # Verify existing session preserved
        assert self.session_manager.get_session("+1000000000") == "thread_existing"
        
        # Verify migrated sessions added
        assert self.session_manager.get_session("+1234567890") == "thread_migrated_1"
        assert self.session_manager.get_session("+1987654321") == "thread_migrated_2"
        
        # Verify metrics account for both existing and migrated
        assert final_metrics['total_sessions_created'] == initial_metrics['total_sessions_created'] + 2

    def test_migrate_overwrites_duplicate_phones(self):
        """Test migration overwrites existing sessions for same phone numbers."""
        # Create existing session
        self.session_manager.set_session("+1234567890", "thread_original")
        original_session = self.session_manager._sessions["+1234567890"]
        
        # Migrate with same phone number
        legacy_sessions = {
            "+1234567890": "thread_overwrite",
            "+1987654321": "thread_new"
        }
        
        migrated_count = self.session_manager.migrate_from_dict(legacy_sessions)
        
        assert migrated_count == 2
        assert len(self.session_manager._sessions) == 2
        
        # Verify session overwritten
        assert self.session_manager.get_session("+1234567890") == "thread_overwrite"
        assert self.session_manager.get_session("+1987654321") == "thread_new"
        
        # Verify timestamps updated for overwritten session
        new_session = self.session_manager._sessions["+1234567890"]
        assert new_session.created_at > original_session.created_at

    def test_migration_timestamps_consistency(self):
        """Test migration sets consistent timestamps for all sessions."""
        legacy_sessions = {
            "+1234567890": "thread_1",
            "+1987654321": "thread_2",
            "+1555555555": "thread_3"
        }
        
        migration_start = datetime.now()
        self.session_manager.migrate_from_dict(legacy_sessions)
        migration_end = datetime.now()
        
        # Verify all sessions have timestamps within migration window
        for phone, entry in self.session_manager._sessions.items():
            assert migration_start <= entry.created_at <= migration_end
            assert migration_start <= entry.last_accessed <= migration_end
            assert entry.created_at == entry.last_accessed  # Should be same for migration

    def test_migration_with_large_dataset(self):
        """Test migration performance with larger dataset."""
        # Create large legacy dataset
        large_sessions = {}
        for i in range(100):
            phone = f"+1{i:09d}"  # Generate phone numbers
            thread_id = f"thread_large_{i:03d}"
            large_sessions[phone] = thread_id
        
        migration_start = datetime.now()
        migrated_count = self.session_manager.migrate_from_dict(large_sessions)
        migration_duration = (datetime.now() - migration_start).total_seconds()
        
        assert migrated_count == 100
        assert len(self.session_manager._sessions) == 100
        
        # Migration should complete quickly (under 1 second for 100 items)
        assert migration_duration < 1.0
        
        # Verify random samples work correctly
        assert self.session_manager.get_session("+1000000005") == "thread_large_005"
        assert self.session_manager.get_session("+1000000050") == "thread_large_050"
        assert self.session_manager.get_session("+1000000099") == "thread_large_099"

    def test_migration_logging_and_metrics(self):
        """Test migration generates appropriate logs and metrics."""
        legacy_sessions = {
            "+1234567890": "thread_1",
            "+1987654321": None,  # Will be skipped
            "+1555555555": "thread_2"
        }
        
        initial_metrics = self.session_manager.get_metrics()
        
        with patch('app.session_manager.log') as mock_log:
            migrated_count = self.session_manager.migrate_from_dict(legacy_sessions)
        
        # Verify migration count
        assert migrated_count == 2
        
        # Verify logging called
        mock_log.info.assert_called_once()
        log_call = mock_log.info.call_args[0][0]
        assert log_call == "sessions_migrated"
        
        log_kwargs = mock_log.info.call_args[1]
        assert log_kwargs['migrated_count'] == 2
        assert log_kwargs['skipped_count'] == 1
        
        # Verify metrics updated correctly
        final_metrics = self.session_manager.get_metrics()
        assert final_metrics['total_sessions_created'] == initial_metrics['total_sessions_created'] + 2

    def test_migration_after_expiration_cleanup(self):
        """Test migration works correctly after expired sessions are cleaned up."""
        # Create expired session
        expired_time = datetime.now() - timedelta(seconds=7200)  # 2 hours ago
        self.session_manager._sessions["+1000000000"] = SessionEntry(
            thread_id="thread_expired",
            created_at=expired_time,
            last_accessed=expired_time
        )
        
        # Run cleanup
        cleanup_count = self.session_manager.cleanup_expired_sessions()
        assert cleanup_count == 1
        assert len(self.session_manager._sessions) == 0
        
        # Now migrate new sessions
        legacy_sessions = {
            "+1234567890": "thread_after_cleanup_1",
            "+1987654321": "thread_after_cleanup_2"
        }
        
        migrated_count = self.session_manager.migrate_from_dict(legacy_sessions)
        
        assert migrated_count == 2
        assert len(self.session_manager._sessions) == 2
        assert self.session_manager.get_session("+1234567890") == "thread_after_cleanup_1"
        assert self.session_manager.get_session("+1987654321") == "thread_after_cleanup_2"

    def test_migration_edge_cases(self):
        """Test migration handles edge cases properly."""
        # Test with various edge case values
        edge_case_sessions = {
            "": "thread_empty_phone",           # Empty phone
            "+1": "thread_short_phone",         # Very short phone
            "+1" + "9" * 50: "thread_long_phone",  # Very long phone
            "+1234567890": "",                  # Empty thread (should skip)
            "+1111111111": "thread_" + "x" * 100,  # Very long thread ID
            "+1222222222": "thread_unicode_🔧",     # Unicode in thread ID
        }
        
        migrated_count = self.session_manager.migrate_from_dict(edge_case_sessions)
        
        # Should migrate all entries with valid thread_ids
        expected_migrated = 5  # All except empty thread
        assert migrated_count == expected_migrated
        
        # Verify edge cases handled correctly
        assert self.session_manager.get_session("") == "thread_empty_phone"
        assert self.session_manager.get_session("+1") == "thread_short_phone"
        assert self.session_manager.get_session("+1234567890") is None  # Skipped
        
        long_phone = "+1" + "9" * 50
        assert self.session_manager.get_session(long_phone) == "thread_long_phone"

    def test_migration_thread_safety(self):
        """Test migration is thread-safe with concurrent operations."""
        import threading
        import time
        
        legacy_sessions = {}
        for i in range(20):
            legacy_sessions[f"+1{i:09d}"] = f"thread_{i}"
        
        results = {}
        
        def migrate_sessions():
            """Migrate sessions in separate thread."""
            results['migrated'] = self.session_manager.migrate_from_dict(legacy_sessions)
        
        def access_sessions():
            """Access sessions during migration."""
            time.sleep(0.01)  # Small delay to interleave with migration
            results['accessed'] = []
            for i in range(5):
                phone = f"+1{i:09d}"
                thread_id = self.session_manager.get_session(phone)
                results['accessed'].append((phone, thread_id))
        
        # Run migration and access concurrently
        migrate_thread = threading.Thread(target=migrate_sessions)
        access_thread = threading.Thread(target=access_sessions)
        
        migrate_thread.start()
        access_thread.start()
        
        migrate_thread.join()
        access_thread.join()
        
        # Verify migration completed
        assert results['migrated'] == 20
        
        # Verify concurrent access didn't cause issues
        assert len(results['accessed']) == 5
        for phone, thread_id in results['accessed']:
            # Thread ID should either be None (if accessed before migration of that entry)
            # or the correct migrated value
            if thread_id is not None:
                expected_id = legacy_sessions[phone]
                assert thread_id == expected_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])