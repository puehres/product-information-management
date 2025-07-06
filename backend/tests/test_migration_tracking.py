"""
Tests for migration tracking functionality.

Tests cover:
- Migration state tracking
- Checksum validation
- Error handling for modified migrations
- Migration ordering and dependencies
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

from app.core.migration_manager import MigrationManager
from app.utils.migration_utils import (
    discover_migration_files,
    validate_migration_dependencies,
    get_migration_dependencies,
    format_migration_summary,
    create_migration_backup_info
)


class TestMigrationTracking:
    """Test migration state tracking functionality."""
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """Create a temporary migrations directory with test files."""
        temp_dir = tempfile.mkdtemp()
        migrations_dir = Path(temp_dir) / "migrations"
        migrations_dir.mkdir()
        
        # Create test migration files with dependencies
        test_migrations = {
            "000_migration_tracking.sql": """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    checksum VARCHAR(64)
                );
            """,
            "001_initial_schema.sql": """
                -- DEPENDS ON: 000_migration_tracking
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL
                );
            """,
            "002_add_user_data.sql": """
                -- DEPENDS ON: 001_initial_schema
                INSERT INTO users (email) VALUES ('test@example.com')
                ON CONFLICT (email) DO NOTHING;
            """,
            "003_user_profiles.sql": """
                -- DEPENDS ON: 001_initial_schema
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    name VARCHAR(255)
                );
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
    
    def test_migration_status_empty_database(self, mock_migration_manager):
        """Test migration status when no migrations have been applied."""
        manager = mock_migration_manager
        
        with patch.object(manager, 'get_applied_migrations') as mock_applied:
            mock_applied.return_value = set()
            
            with patch.object(manager, 'validate_migration_integrity') as mock_integrity:
                mock_integrity.return_value = (True, [])
                
                status = manager.get_migration_status()
                
                assert status['total_migrations'] == 4
                assert status['applied_count'] == 0
                assert status['pending_count'] == 4
                assert status['integrity_valid'] is True
                assert len(status['integrity_issues']) == 0
                assert len(status['pending_migrations']) == 4
    
    def test_migration_status_partially_applied(self, mock_migration_manager):
        """Test migration status when some migrations have been applied."""
        manager = mock_migration_manager
        
        with patch.object(manager, 'get_applied_migrations') as mock_applied:
            mock_applied.return_value = {"000_migration_tracking", "001_initial_schema"}
            
            with patch.object(manager, 'validate_migration_integrity') as mock_integrity:
                mock_integrity.return_value = (True, [])
                
                status = manager.get_migration_status()
                
                assert status['total_migrations'] == 4
                assert status['applied_count'] == 2
                assert status['pending_count'] == 2
                assert "000_migration_tracking" in status['applied_migrations']
                assert "001_initial_schema" in status['applied_migrations']
                assert "002_add_user_data" in status['pending_migrations']
                assert "003_user_profiles" in status['pending_migrations']
    
    def test_migration_status_all_applied(self, mock_migration_manager):
        """Test migration status when all migrations have been applied."""
        manager = mock_migration_manager
        
        with patch.object(manager, 'get_applied_migrations') as mock_applied:
            mock_applied.return_value = {
                "000_migration_tracking", 
                "001_initial_schema", 
                "002_add_user_data", 
                "003_user_profiles"
            }
            
            with patch.object(manager, 'validate_migration_integrity') as mock_integrity:
                mock_integrity.return_value = (True, [])
                
                status = manager.get_migration_status()
                
                assert status['total_migrations'] == 4
                assert status['applied_count'] == 4
                assert status['pending_count'] == 0
                assert len(status['pending_migrations']) == 0
    
    def test_migration_status_with_integrity_issues(self, mock_migration_manager):
        """Test migration status when there are integrity issues."""
        manager = mock_migration_manager
        
        with patch.object(manager, 'get_applied_migrations') as mock_applied:
            mock_applied.return_value = {"000_migration_tracking"}
            
            with patch.object(manager, 'validate_migration_integrity') as mock_integrity:
                mock_integrity.return_value = (False, ["Migration file modified: 000_migration_tracking.sql"])
                
                status = manager.get_migration_status()
                
                assert status['integrity_valid'] is False
                assert len(status['integrity_issues']) == 1
                assert "modified" in status['integrity_issues'][0]


class TestChecksumValidation:
    """Test checksum validation for migration integrity."""
    
    @pytest.fixture
    def temp_migration_file(self):
        """Create a temporary migration file."""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "001_test.sql"
        file_path.write_text("SELECT 1;")
        
        yield file_path
        
        shutil.rmtree(temp_dir)
    
    def test_checksum_calculation_consistency(self, temp_migration_file):
        """Test that checksum calculation is consistent."""
        from app.utils.migration_utils import calculate_file_checksum
        
        checksum1 = calculate_file_checksum(temp_migration_file)
        checksum2 = calculate_file_checksum(temp_migration_file)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length
    
    def test_checksum_changes_with_content(self, temp_migration_file):
        """Test that checksum changes when file content changes."""
        from app.utils.migration_utils import calculate_file_checksum
        
        # Calculate initial checksum
        checksum1 = calculate_file_checksum(temp_migration_file)
        
        # Modify file content
        temp_migration_file.write_text("SELECT 2;")
        
        # Calculate new checksum
        checksum2 = calculate_file_checksum(temp_migration_file)
        
        assert checksum1 != checksum2
    
    def test_checksum_validation_with_manager(self):
        """Test checksum validation through MigrationManager."""
        with patch('app.core.migration_manager.get_settings') as mock_settings:
            mock_settings.return_value.supabase_database_url = "postgresql://test:test@localhost/test"
            
            manager = MigrationManager()
            
            # Create a temporary file
            temp_dir = tempfile.mkdtemp()
            try:
                manager.migrations_dir = Path(temp_dir)
                test_file = manager.migrations_dir / "001_test.sql"
                test_file.write_text("SELECT 1;")
                
                # Calculate checksum
                checksum = manager.calculate_checksum(test_file)
                
                # Mock database response with matching checksum
                with patch.object(manager, 'get_database_connection') as mock_conn:
                    mock_cursor = MagicMock()
                    mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
                    mock_cursor.fetchall.return_value = [
                        {"version": "001_test", "checksum": checksum}
                    ]
                    
                    is_valid, issues = manager.validate_migration_integrity()
                    
                    assert is_valid is True
                    assert len(issues) == 0
                    
            finally:
                shutil.rmtree(temp_dir)


class TestMigrationDependencies:
    """Test migration dependency validation."""
    
    @pytest.fixture
    def temp_migrations_with_deps(self):
        """Create migrations with dependency declarations."""
        temp_dir = tempfile.mkdtemp()
        migrations_dir = Path(temp_dir) / "migrations"
        migrations_dir.mkdir()
        
        migrations = {
            "001_base.sql": """
                CREATE TABLE base_table (id SERIAL PRIMARY KEY);
            """,
            "002_depends_on_base.sql": """
                -- DEPENDS ON: 001_base
                ALTER TABLE base_table ADD COLUMN name VARCHAR(100);
            """,
            "003_multiple_deps.sql": """
                -- DEPENDS ON: 001_base, 002_depends_on_base
                CREATE INDEX idx_base_name ON base_table(name);
            """,
            "004_no_deps.sql": """
                CREATE TABLE independent_table (id SERIAL PRIMARY KEY);
            """
        }
        
        for filename, content in migrations.items():
            (migrations_dir / filename).write_text(content.strip())
        
        yield migrations_dir
        
        shutil.rmtree(temp_dir)
    
    def test_get_migration_dependencies(self, temp_migrations_with_deps):
        """Test extracting dependencies from migration files."""
        files = discover_migration_files(temp_migrations_with_deps)
        
        # Test file with no dependencies
        content1 = files[0].read_text()
        deps1 = get_migration_dependencies(content1)
        assert len(deps1) == 0
        
        # Test file with single dependency
        content2 = files[1].read_text()
        deps2 = get_migration_dependencies(content2)
        assert len(deps2) == 1
        assert "001_base" in deps2
        
        # Test file with multiple dependencies
        content3 = files[2].read_text()
        deps3 = get_migration_dependencies(content3)
        assert len(deps3) == 2
        assert "001_base" in deps3
        assert "002_depends_on_base" in deps3
    
    def test_validate_migration_dependencies_satisfied(self, temp_migrations_with_deps):
        """Test dependency validation when all dependencies are satisfied."""
        files = discover_migration_files(temp_migrations_with_deps)
        applied_migrations = {"001_base", "002_depends_on_base"}
        
        is_satisfied, issues = validate_migration_dependencies(files, applied_migrations)
        
        # Should be satisfied because 003_multiple_deps depends on applied migrations
        # and 004_no_deps has no dependencies
        assert is_satisfied is True
        assert len(issues) == 0
    
    def test_validate_migration_dependencies_unsatisfied(self, temp_migrations_with_deps):
        """Test dependency validation when dependencies are not satisfied."""
        files = discover_migration_files(temp_migrations_with_deps)
        applied_migrations = {"001_base"}  # Missing 002_depends_on_base
        
        is_satisfied, issues = validate_migration_dependencies(files, applied_migrations)
        
        # Should fail because 003_multiple_deps depends on 002_depends_on_base which is not applied
        assert is_satisfied is False
        assert len(issues) > 0
        assert any("002_depends_on_base" in issue for issue in issues)


class TestMigrationOrdering:
    """Test migration file ordering and execution sequence."""
    
    def test_migration_file_ordering(self):
        """Test that migration files are ordered correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            migrations_dir = Path(temp_dir) / "migrations"
            migrations_dir.mkdir()
            
            # Create files in random order
            files_to_create = [
                "003_third.sql",
                "001_first.sql", 
                "010_tenth.sql",
                "002_second.sql"
            ]
            
            for filename in files_to_create:
                (migrations_dir / filename).write_text("SELECT 1;")
            
            # Discover and check ordering
            discovered_files = discover_migration_files(migrations_dir)
            
            assert len(discovered_files) == 4
            assert discovered_files[0].name == "001_first.sql"
            assert discovered_files[1].name == "002_second.sql"
            assert discovered_files[2].name == "003_third.sql"
            assert discovered_files[3].name == "010_tenth.sql"
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_migration_summary_formatting(self):
        """Test formatting of migration status summary."""
        temp_dir = tempfile.mkdtemp()
        try:
            migrations_dir = Path(temp_dir) / "migrations"
            migrations_dir.mkdir()
            
            # Create test files
            (migrations_dir / "001_first.sql").write_text("SELECT 1;")
            (migrations_dir / "002_second.sql").write_text("SELECT 2;")
            (migrations_dir / "003_third.sql").write_text("SELECT 3;")
            
            files = discover_migration_files(migrations_dir)
            applied_versions = {"001_first", "002_second"}
            
            summary = format_migration_summary(files, applied_versions)
            
            assert "Total migrations: 3" in summary
            assert "Applied: 2" in summary
            assert "Pending: 1" in summary
            assert "001_first.sql: ✅ Applied" in summary
            assert "002_second.sql: ✅ Applied" in summary
            assert "003_third.sql: ⏳ Pending" in summary
            
        finally:
            shutil.rmtree(temp_dir)


class TestMigrationBackupInfo:
    """Test migration backup and metadata functionality."""
    
    def test_create_migration_backup_info(self):
        """Test creating backup information for migration files."""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = Path(temp_dir) / "001_test.sql"
            content = "CREATE TABLE test (id SERIAL PRIMARY KEY);"
            test_file.write_text(content)
            
            backup_info = create_migration_backup_info(test_file)
            
            assert backup_info['version'] == "001_test"
            assert backup_info['filename'] == "001_test.sql"
            assert 'checksum' in backup_info
            assert backup_info['size_bytes'] == len(content)
            assert backup_info['line_count'] == 1
            assert backup_info['has_dependencies'] is False
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_create_migration_backup_info_with_dependencies(self):
        """Test backup info for migration with dependencies."""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = Path(temp_dir) / "002_with_deps.sql"
            content = """
            -- DEPENDS ON: 001_base
            CREATE TABLE dependent (
                id SERIAL PRIMARY KEY,
                base_id INTEGER REFERENCES base_table(id)
            );
            """
            test_file.write_text(content.strip())
            
            backup_info = create_migration_backup_info(test_file)
            
            assert backup_info['version'] == "002_with_deps"
            assert backup_info['has_dependencies'] is True
            assert backup_info['line_count'] == 5
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_create_migration_backup_info_error_handling(self):
        """Test backup info creation with file errors."""
        # Test with non-existent file
        non_existent_file = Path("/non/existent/file.sql")
        backup_info = create_migration_backup_info(non_existent_file)
        
        assert backup_info['version'] == "file"
        assert backup_info['filename'] == "file.sql"
        assert 'error' in backup_info


class TestMigrationErrorHandling:
    """Test error handling in migration system."""
    
    def test_migration_manager_invalid_database_url(self):
        """Test MigrationManager with invalid database URL."""
        with patch('app.core.migration_manager.get_settings') as mock_settings:
            mock_settings.return_value.supabase_database_url = None
            
            with pytest.raises(ValueError, match="SUPABASE_DATABASE_URL not found"):
                MigrationManager()
    
    def test_migration_manager_database_connection_error(self):
        """Test MigrationManager with database connection errors."""
        with patch('app.core.migration_manager.get_settings') as mock_settings:
            mock_settings.return_value.supabase_database_url = "postgresql://test:test@localhost/test"
            
            manager = MigrationManager()
            
            with patch('app.core.migration_manager.psycopg2.connect') as mock_connect:
                mock_connect.side_effect = Exception("Connection failed")
                
                # Test ensure_tracking_table with connection error
                with pytest.raises(Exception, match="Connection failed"):
                    manager.ensure_tracking_table()
    
    def test_checksum_calculation_file_not_found(self):
        """Test checksum calculation with non-existent file."""
        with patch('app.core.migration_manager.get_settings') as mock_settings:
            mock_settings.return_value.supabase_database_url = "postgresql://test:test@localhost/test"
            
            manager = MigrationManager()
            non_existent_file = Path("/non/existent/file.sql")
            
            with pytest.raises(FileNotFoundError):
                manager.calculate_checksum(non_existent_file)
    
    def test_migration_validation_with_invalid_content(self):
        """Test migration validation with problematic content."""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = Path(temp_dir) / "bad_migration.sql"
            
            # Test with dangerous operations
            dangerous_content = """
            DROP TABLE users;
            CREATE TYPE status AS ENUM ('active');
            ALTER TABLE products DROP COLUMN price;
            """
            
            is_valid, warnings = validate_migration_content(dangerous_content, test_file)
            
            # Should be valid but with warnings
            assert is_valid is True
            assert len(warnings) >= 2  # Should warn about DROP operations
            
        finally:
            shutil.rmtree(temp_dir)
