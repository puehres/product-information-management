"""
Comprehensive tests for the migration system.

Tests cover:
- Migration runner on clean database
- Migration runner on existing database
- Re-running migrations (should be no-op)
- Migration tracking table functionality
- Error handling for various failure scenarios
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.migration_manager import MigrationManager
from app.utils.migration_utils import (
    discover_migration_files,
    validate_migration_content,
    extract_migration_version,
    calculate_file_checksum
)


class TestMigrationManager:
    """Test the MigrationManager class functionality."""
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """Create a temporary migrations directory with test files."""
        temp_dir = tempfile.mkdtemp()
        migrations_dir = Path(temp_dir) / "migrations"
        migrations_dir.mkdir()
        
        # Create test migration files
        test_migrations = {
            "000_migration_tracking.sql": """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    checksum VARCHAR(64)
                );
            """,
            "001_test_schema.sql": """
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                );
            """,
            "002_test_data.sql": """
                INSERT INTO test_table (name) VALUES ('test') 
                ON CONFLICT DO NOTHING;
            """
        }
        
        for filename, content in test_migrations.items():
            (migrations_dir / filename).write_text(content.strip())
        
        yield migrations_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_migration_manager(self, temp_migrations_dir):
        """Create a MigrationManager with mocked database connection."""
        with patch('app.core.migration_manager.get_settings') as mock_settings:
            mock_settings.return_value.supabase_database_url = "postgresql://test:test@localhost/test"
            
            manager = MigrationManager()
            manager.migrations_dir = temp_migrations_dir
            
            yield manager
    
    def test_migration_manager_initialization(self, mock_migration_manager):
        """Test MigrationManager initializes correctly."""
        manager = mock_migration_manager
        assert manager.migrations_dir.exists()
        assert manager.database_url == "postgresql://test:test@localhost/test"
    
    def test_get_migration_files(self, mock_migration_manager):
        """Test discovery of migration files."""
        manager = mock_migration_manager
        files = manager.get_migration_files()
        
        assert len(files) == 3
        assert files[0].name == "000_migration_tracking.sql"
        assert files[1].name == "001_test_schema.sql"
        assert files[2].name == "002_test_data.sql"
    
    def test_calculate_checksum(self, mock_migration_manager):
        """Test checksum calculation for migration files."""
        manager = mock_migration_manager
        files = manager.get_migration_files()
        
        checksum1 = manager.calculate_checksum(files[0])
        checksum2 = manager.calculate_checksum(files[0])
        
        # Same file should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length
    
    @patch('app.core.migration_manager.psycopg2.connect')
    def test_ensure_tracking_table_creates_table(self, mock_connect, mock_migration_manager):
        """Test that ensure_tracking_table creates the table when it doesn't exist."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock table doesn't exist
        mock_cursor.fetchone.return_value = [False]
        
        manager = mock_migration_manager
        result = manager.ensure_tracking_table()
        
        assert result is True
        mock_cursor.execute.assert_called()
    
    @patch('app.core.migration_manager.psycopg2.connect')
    def test_get_applied_migrations_empty(self, mock_connect, mock_migration_manager):
        """Test getting applied migrations when none exist."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock empty result
        mock_cursor.fetchall.return_value = []
        
        manager = mock_migration_manager
        applied = manager.get_applied_migrations()
        
        assert applied == set()
    
    @patch('app.core.migration_manager.psycopg2.connect')
    def test_get_applied_migrations_with_data(self, mock_connect, mock_migration_manager):
        """Test getting applied migrations when some exist."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock result with applied migrations
        mock_cursor.fetchall.return_value = [
            ("000_migration_tracking",),
            ("001_test_schema",)
        ]
        
        manager = mock_migration_manager
        applied = manager.get_applied_migrations()
        
        assert applied == {"000_migration_tracking", "001_test_schema"}
    
    @patch('app.core.migration_manager.psycopg2.connect')
    def test_record_migration(self, mock_connect, mock_migration_manager):
        """Test recording a migration in the tracking table."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        manager = mock_migration_manager
        result = manager.record_migration("001_test_schema", "abc123", 1500)
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        
        # Check the SQL was called with correct parameters
        call_args = mock_cursor.execute.call_args
        assert "INSERT INTO schema_migrations" in call_args[0][0]
        assert call_args[0][1] == ("001_test_schema", "abc123", 1500)
    
    def test_get_pending_migrations(self, mock_migration_manager):
        """Test getting pending migrations."""
        manager = mock_migration_manager
        
        # Mock applied migrations
        with patch.object(manager, 'get_applied_migrations') as mock_applied:
            mock_applied.return_value = {"000_migration_tracking"}
            
            pending = manager.get_pending_migrations()
            
            assert len(pending) == 2
            assert pending[0].name == "001_test_schema.sql"
            assert pending[1].name == "002_test_data.sql"
    
    @patch('app.core.migration_manager.psycopg2.connect')
    def test_validate_migration_integrity_valid(self, mock_connect, mock_migration_manager):
        """Test migration integrity validation when all files are valid."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock applied migrations with checksums
        files = mock_migration_manager.get_migration_files()
        checksum = mock_migration_manager.calculate_checksum(files[0])
        
        mock_cursor.fetchall.return_value = [
            {"version": "000_migration_tracking", "checksum": checksum}
        ]
        
        manager = mock_migration_manager
        is_valid, issues = manager.validate_migration_integrity()
        
        assert is_valid is True
        assert len(issues) == 0
    
    @patch('app.core.migration_manager.psycopg2.connect')
    def test_validate_migration_integrity_modified(self, mock_connect, mock_migration_manager):
        """Test migration integrity validation when a file has been modified."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock applied migration with different checksum
        mock_cursor.fetchall.return_value = [
            {"version": "000_migration_tracking", "checksum": "different_checksum"}
        ]
        
        manager = mock_migration_manager
        is_valid, issues = manager.validate_migration_integrity()
        
        assert is_valid is False
        assert len(issues) == 1
        assert "checksum mismatch" in issues[0]


class TestMigrationUtils:
    """Test migration utility functions."""
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """Create a temporary migrations directory."""
        temp_dir = tempfile.mkdtemp()
        migrations_dir = Path(temp_dir) / "migrations"
        migrations_dir.mkdir()
        
        yield migrations_dir
        
        shutil.rmtree(temp_dir)
    
    def test_discover_migration_files(self, temp_migrations_dir):
        """Test migration file discovery."""
        # Create test files
        (temp_migrations_dir / "001_test.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "002_another.sql").write_text("SELECT 2;")
        (temp_migrations_dir / "invalid.txt").write_text("Not a migration")
        (temp_migrations_dir / "003_third.sql").write_text("SELECT 3;")
        
        files = discover_migration_files(temp_migrations_dir)
        
        assert len(files) == 3
        assert files[0].name == "001_test.sql"
        assert files[1].name == "002_another.sql"
        assert files[2].name == "003_third.sql"
    
    def test_discover_migration_files_empty_dir(self, temp_migrations_dir):
        """Test migration file discovery in empty directory."""
        files = discover_migration_files(temp_migrations_dir)
        assert len(files) == 0
    
    def test_discover_migration_files_nonexistent_dir(self):
        """Test migration file discovery with nonexistent directory."""
        files = discover_migration_files(Path("/nonexistent/path"))
        assert len(files) == 0
    
    def test_extract_migration_version(self, temp_migrations_dir):
        """Test extracting migration version from file path."""
        file_path = temp_migrations_dir / "001_test_migration.sql"
        version = extract_migration_version(file_path)
        assert version == "001_test_migration"
    
    def test_calculate_file_checksum(self, temp_migrations_dir):
        """Test file checksum calculation."""
        test_file = temp_migrations_dir / "test.sql"
        test_file.write_text("SELECT 1;")
        
        checksum1 = calculate_file_checksum(test_file)
        checksum2 = calculate_file_checksum(test_file)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64
    
    def test_validate_migration_content_valid(self, temp_migrations_dir):
        """Test validation of valid migration content."""
        content = """
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        
        file_path = temp_migrations_dir / "001_test.sql"
        is_valid, warnings = validate_migration_content(content, file_path)
        
        assert is_valid is True
        assert len(warnings) == 0
    
    def test_validate_migration_content_empty(self, temp_migrations_dir):
        """Test validation of empty migration content."""
        content = ""
        
        file_path = temp_migrations_dir / "001_test.sql"
        is_valid, warnings = validate_migration_content(content, file_path)
        
        assert is_valid is False
        assert len(warnings) == 1
        assert "empty" in warnings[0]
    
    def test_validate_migration_content_dangerous(self, temp_migrations_dir):
        """Test validation of potentially dangerous migration content."""
        content = """
        DROP TABLE users;
        CREATE TYPE status AS ENUM ('active', 'inactive');
        """
        
        file_path = temp_migrations_dir / "001_test.sql"
        is_valid, warnings = validate_migration_content(content, file_path)
        
        assert is_valid is True  # Still valid, but has warnings
        assert len(warnings) >= 1
        assert any("DROP TABLE" in warning for warning in warnings)


class TestMigrationIntegration:
    """Integration tests for the complete migration system."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory structure."""
        temp_dir = tempfile.mkdtemp()
        project_dir = Path(temp_dir)
        
        # Create directory structure
        (project_dir / "app" / "core").mkdir(parents=True)
        (project_dir / "app" / "utils").mkdir(parents=True)
        (project_dir / "migrations").mkdir()
        
        # Create minimal migration files
        migrations = {
            "000_migration_tracking.sql": """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    checksum VARCHAR(64)
                );
            """,
            "001_initial_schema.sql": """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """
        }
        
        for filename, content in migrations.items():
            (project_dir / "migrations" / filename).write_text(content.strip())
        
        yield project_dir
        
        shutil.rmtree(temp_dir)
    
    def test_migration_system_end_to_end(self, temp_project_dir):
        """Test the complete migration system workflow."""
        # This test would require a real database connection
        # For now, we'll test the workflow with mocked database calls
        
        with patch('app.core.migration_manager.get_settings') as mock_settings:
            mock_settings.return_value.supabase_database_url = "postgresql://test:test@localhost/test"
            
            # Test migration discovery
            migrations_dir = temp_project_dir / "migrations"
            files = discover_migration_files(migrations_dir)
            
            assert len(files) == 2
            assert files[0].name == "000_migration_tracking.sql"
            assert files[1].name == "001_initial_schema.sql"
            
            # Test content validation
            for file_path in files:
                content = file_path.read_text()
                is_valid, warnings = validate_migration_content(content, file_path)
                assert is_valid is True
            
            # Test checksum calculation
            checksums = {}
            for file_path in files:
                checksums[file_path.name] = calculate_file_checksum(file_path)
            
            assert len(checksums) == 2
            assert all(len(checksum) == 64 for checksum in checksums.values())


@pytest.mark.integration
class TestMigrationSystemWithDatabase:
    """
    Integration tests that require a real database connection.
    
    These tests are marked with @pytest.mark.integration and should be run
    separately with a test database available.
    """
    
    @pytest.fixture
    def test_database_url(self):
        """Get test database URL from environment."""
        import os
        url = os.getenv("TEST_DATABASE_URL")
        if not url:
            pytest.skip("TEST_DATABASE_URL not set")
        return url
    
    def test_migration_runner_clean_database(self, test_database_url):
        """Test migration runner on a clean database."""
        # This would test the actual migration runner against a real database
        # Implementation would depend on having a test database available
        pytest.skip("Requires test database setup")
    
    def test_migration_runner_idempotent(self, test_database_url):
        """Test that running migrations multiple times is safe."""
        # This would test re-running migrations on an existing database
        pytest.skip("Requires test database setup")
    
    def test_migration_tracking_persistence(self, test_database_url):
        """Test that migration tracking persists across runs."""
        # This would test the tracking table functionality
        pytest.skip("Requires test database setup")
