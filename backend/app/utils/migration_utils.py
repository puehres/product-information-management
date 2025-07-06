"""
Migration utility functions for the Universal Product Automation System.

This module provides helper functions for migration file operations,
checksum calculations, and migration discovery.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def discover_migration_files(migrations_dir: Path) -> List[Path]:
    """
    Discover and sort migration files in the migrations directory.
    
    Args:
        migrations_dir (Path): Path to the migrations directory
        
    Returns:
        List[Path]: Sorted list of migration file paths
    """
    if not migrations_dir.exists():
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return []
    
    # Find all .sql files
    sql_files = list(migrations_dir.glob("*.sql"))
    
    # Filter and sort by filename (ensures proper execution order)
    migration_files = []
    for file_path in sql_files:
        if file_path.is_file() and is_valid_migration_filename(file_path.name):
            migration_files.append(file_path)
    
    # Sort by filename to ensure correct execution order
    migration_files.sort(key=lambda x: x.name)
    
    logger.debug(f"Discovered {len(migration_files)} migration files in {migrations_dir}")
    return migration_files


def is_valid_migration_filename(filename: str) -> bool:
    """
    Check if a filename follows the migration naming convention.
    
    Expected format: NNN_description.sql (e.g., 001_initial_schema.sql)
    
    Args:
        filename (str): The filename to validate
        
    Returns:
        bool: True if filename follows the convention
    """
    # Pattern: starts with digits, followed by underscore, then description, ends with .sql
    pattern = r'^\d{3}_[a-zA-Z0-9_-]+\.sql$'
    return bool(re.match(pattern, filename))


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path (Path): Path to the file
        
    Returns:
        str: SHA-256 checksum as hexadecimal string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise


def read_migration_file(file_path: Path) -> str:
    """
    Read the contents of a migration file.
    
    Args:
        file_path (Path): Path to the migration file
        
    Returns:
        str: File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
        UnicodeDecodeError: If file contains invalid UTF-8
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"Migration file is empty: {file_path}")
        
        return content
    except (FileNotFoundError, IOError, UnicodeDecodeError) as e:
        logger.error(f"Failed to read migration file {file_path}: {e}")
        raise


def extract_migration_version(file_path: Path) -> str:
    """
    Extract the migration version from a file path.
    
    Args:
        file_path (Path): Path to the migration file
        
    Returns:
        str: Migration version (filename without extension)
    """
    return file_path.stem


def validate_migration_content(content: str, file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate migration file content for common issues.
    
    Args:
        content (str): Migration file content
        file_path (Path): Path to the migration file (for error reporting)
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_warnings)
    """
    warnings = []
    
    # Check for empty content
    if not content.strip():
        warnings.append(f"Migration file is empty: {file_path.name}")
        return False, warnings
    
    # Check for dangerous operations without safety checks
    dangerous_patterns = [
        (r'\bDROP\s+TABLE\s+(?!IF\s+EXISTS)', "DROP TABLE without IF EXISTS"),
        (r'\bCREATE\s+TYPE\s+(?!.*IF\s+NOT\s+EXISTS)', "CREATE TYPE without existence check"),
        (r'\bALTER\s+TABLE\s+.*\bDROP\s+COLUMN\s+(?!IF\s+EXISTS)', "DROP COLUMN without IF EXISTS"),
    ]
    
    for pattern, description in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"Potentially unsafe operation in {file_path.name}: {description}")
    
    # Check for recommended patterns
    recommended_patterns = [
        (r'\bCREATE\s+TABLE\s+IF\s+NOT\s+EXISTS', "Uses CREATE TABLE IF NOT EXISTS"),
        (r'\bCREATE\s+INDEX\s+IF\s+NOT\s+EXISTS', "Uses CREATE INDEX IF NOT EXISTS"),
    ]
    
    has_recommended = False
    for pattern, description in recommended_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            has_recommended = True
            break
    
    if not has_recommended and 'CREATE' in content.upper():
        warnings.append(f"Consider using IF NOT EXISTS patterns in {file_path.name}")
    
    return True, warnings


def format_migration_summary(migration_files: List[Path], applied_versions: set) -> str:
    """
    Format a summary of migration status.
    
    Args:
        migration_files (List[Path]): List of all migration files
        applied_versions (set): Set of applied migration versions
        
    Returns:
        str: Formatted summary string
    """
    lines = []
    lines.append(f"Migration Summary:")
    lines.append(f"  Total migrations: {len(migration_files)}")
    lines.append(f"  Applied: {len(applied_versions)}")
    lines.append(f"  Pending: {len(migration_files) - len(applied_versions)}")
    lines.append("")
    
    if migration_files:
        lines.append("Migration Status:")
        for file_path in migration_files:
            version = extract_migration_version(file_path)
            status = "✅ Applied" if version in applied_versions else "⏳ Pending"
            lines.append(f"  {file_path.name}: {status}")
    
    return "\n".join(lines)


def get_migration_dependencies(content: str) -> List[str]:
    """
    Extract migration dependencies from SQL content.
    
    This function looks for comments indicating dependencies on other migrations.
    Format: -- DEPENDS ON: 001_initial_schema, 002_seed_data
    
    Args:
        content (str): Migration file content
        
    Returns:
        List[str]: List of dependency migration versions
    """
    dependencies = []
    
    # Look for dependency comments
    dependency_pattern = r'--\s*DEPENDS\s+ON:\s*([^\n]+)'
    matches = re.findall(dependency_pattern, content, re.IGNORECASE)
    
    for match in matches:
        # Split by comma and clean up
        deps = [dep.strip() for dep in match.split(',')]
        dependencies.extend(deps)
    
    return dependencies


def validate_migration_dependencies(
    migration_files: List[Path], 
    applied_versions: set
) -> Tuple[bool, List[str]]:
    """
    Validate that migration dependencies are satisfied.
    
    Args:
        migration_files (List[Path]): List of all migration files
        applied_versions (set): Set of applied migration versions
        
    Returns:
        Tuple[bool, List[str]]: (dependencies_satisfied, list_of_issues)
    """
    issues = []
    
    for file_path in migration_files:
        version = extract_migration_version(file_path)
        
        # Skip already applied migrations
        if version in applied_versions:
            continue
        
        try:
            content = read_migration_file(file_path)
            dependencies = get_migration_dependencies(content)
            
            for dep in dependencies:
                if dep not in applied_versions:
                    issues.append(f"Migration {version} depends on {dep} which is not applied")
        
        except Exception as e:
            issues.append(f"Cannot check dependencies for {version}: {e}")
    
    return len(issues) == 0, issues


def create_migration_backup_info(file_path: Path) -> Dict[str, Any]:
    """
    Create backup information for a migration file.
    
    Args:
        file_path (Path): Path to the migration file
        
    Returns:
        Dict[str, Any]: Backup information including checksum and metadata
    """
    try:
        content = read_migration_file(file_path)
        checksum = calculate_file_checksum(file_path)
        
        return {
            'version': extract_migration_version(file_path),
            'filename': file_path.name,
            'checksum': checksum,
            'size_bytes': file_path.stat().st_size,
            'content_preview': content[:200] + "..." if len(content) > 200 else content,
            'line_count': len(content.splitlines()),
            'has_dependencies': len(get_migration_dependencies(content)) > 0
        }
    except Exception as e:
        logger.error(f"Failed to create backup info for {file_path}: {e}")
        return {
            'version': extract_migration_version(file_path),
            'filename': file_path.name,
            'error': str(e)
        }
