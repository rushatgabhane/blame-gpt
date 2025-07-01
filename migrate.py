#!/usr/bin/env python3
"""
Database migration runner compatible with golang-migrate conventions
"""
import os
import sqlite3
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional
from libs import constants

class Migration:
    def __init__(self, version: int, name: str, up_file: Path, down_file: Path):
        self.version = version
        self.name = name
        self.up_file = up_file
        self.down_file = down_file
    
    def __repr__(self):
        return f"Migration(version={self.version}, name='{self.name}')"

class MigrationRunner:
    def __init__(self, db_path: str, migrations_dir: str):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.ensure_schema_migrations_table()
    
    def ensure_schema_migrations_table(self):
        """Create schema_migrations table if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    dirty BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            conn.commit()
    
    def get_migrations(self) -> List[Migration]:
        """Get all available migrations sorted by version"""
        migrations = []
        up_files = sorted(self.migrations_dir.glob("*.up.sql"))
        
        for up_file in up_files:
            # Parse filename: 001_initial_tables.up.sql
            match = re.match(r"(\d+)_(.+)\.up\.sql", up_file.name)
            if not match:
                continue
            
            version = int(match.group(1))
            name = match.group(2)
            down_file = up_file.with_name(f"{version:03d}_{name}.down.sql")
            
            if down_file.exists():
                migrations.append(Migration(version, name, up_file, down_file))
        
        return sorted(migrations, key=lambda m: m.version)
    
    def get_current_version(self) -> Optional[int]:
        """Get current migration version"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                result = conn.execute(
                    "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
                ).fetchone()
                return result[0] if result else None
            except sqlite3.OperationalError:
                return None
    
    def set_version(self, version: int, dirty: bool = False):
        """Set migration version"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
            conn.execute(
                "INSERT INTO schema_migrations (version, dirty) VALUES (?, ?)",
                (version, dirty)
            )
            conn.commit()
    
    def remove_version(self, version: int):
        """Remove migration version"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
            conn.commit()
    
    def is_dirty(self) -> bool:
        """Check if database is in dirty state"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT dirty FROM schema_migrations WHERE dirty = TRUE LIMIT 1"
            ).fetchone()
            return result is not None
    
    def apply_migration(self, migration: Migration, direction: str) -> bool:
        """Apply a migration up or down"""
        sql_file = migration.up_file if direction == "up" else migration.down_file
        
        try:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Set dirty state before applying
            self.set_version(migration.version, dirty=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                conn.executescript(sql_content)
                conn.commit()
            
            # Clear dirty state after successful application
            if direction == "up":
                self.set_version(migration.version, dirty=False)
            else:
                self.remove_version(migration.version)
            
            print(f"Applied {direction}: {migration.version}_{migration.name}")
            return True
            
        except Exception as e:
            print(f"Error applying migration {migration.version}_{migration.name} ({direction}): {e}")
            return False
    
    def up(self, target_steps: Optional[int] = None) -> int:
        """Run up migrations"""
        migrations = self.get_migrations()
        current_version = self.get_current_version() or 0
        
        # Get migrations to apply
        pending_migrations = [m for m in migrations if m.version > current_version]
        
        if target_steps is not None:
            pending_migrations = pending_migrations[:target_steps]
        
        if not pending_migrations:
            print("No migrations to apply")
            return 0
        
        success_count = 0
        for migration in pending_migrations:
            if self.apply_migration(migration, "up"):
                success_count += 1
            else:
                return 1
        
        print(f"Applied {success_count} migrations")
        return 0
    
    def down(self, target_steps: Optional[int] = None) -> int:
        """Run down migrations"""
        migrations = self.get_migrations()
        current_version = self.get_current_version()
        
        if current_version is None:
            print("No migrations to rollback")
            return 0
        
        # Get migrations to rollback (in reverse order)
        applied_migrations = [m for m in migrations if m.version <= current_version]
        applied_migrations.reverse()
        
        if target_steps is not None:
            applied_migrations = applied_migrations[:target_steps]
        
        if not applied_migrations:
            print("No migrations to rollback")
            return 0
        
        success_count = 0
        for migration in applied_migrations:
            if self.apply_migration(migration, "down"):
                success_count += 1
            else:
                return 1
        
        print(f"Rolled back {success_count} migrations")
        return 0
    
    def goto(self, target_version: int) -> int:
        """Migrate to specific version"""
        current_version = self.get_current_version() or 0
        
        if target_version == current_version:
            print(f"Already at version {target_version}")
            return 0
        elif target_version > current_version:
            # Need to go up
            migrations = self.get_migrations()
            target_migrations = [m for m in migrations if current_version < m.version <= target_version]
            
            for migration in target_migrations:
                if not self.apply_migration(migration, "up"):
                    return 1
        else:
            # Need to go down
            migrations = self.get_migrations()
            target_migrations = [m for m in migrations if target_version < m.version <= current_version]
            target_migrations.reverse()
            
            for migration in target_migrations:
                if not self.apply_migration(migration, "down"):
                    return 1
        
        print(f"Migrated to version {target_version}")
        return 0
    
    def version(self) -> int:
        """Show current version"""
        current_version = self.get_current_version()
        if current_version is None:
            print("No migrations applied")
        else:
            dirty = " (dirty)" if self.is_dirty() else ""
            print(f"Current version: {current_version}{dirty}")
        return 0
    
    def force(self, version: int) -> int:
        """Force set version without running migration"""
        self.set_version(version, dirty=False)
        print(f"Forced version to {version}")
        return 0

def get_core_runner() -> MigrationRunner:
    """Get migration runner for core database"""
    migrations_dir = str(Path(__file__).parent / "migrations" / "core")
    return MigrationRunner(constants.CACHE_DB_PATH, migrations_dir)

def get_docs_runner() -> MigrationRunner:
    """Get migration runner for docs database"""
    migrations_dir = str(Path(__file__).parent / "migrations" / "docs")
    return MigrationRunner(constants.DOCS_DB_PATH, migrations_dir)

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [args...]")
        print("Commands:")
        print("  up [N]        - Run all or N migrations up")
        print("  down [N]      - Run all or N migrations down")
        print("  goto VERSION  - Migrate to specific version")
        print("  force VERSION - Force set version without running migration")
        print("  version       - Show current migration version")
        print("  create NAME   - Create new migration files")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == "create":
        if not args:
            print("Usage: python migrate.py create <migration_name>")
            sys.exit(1)
        
        migration_name = args[0]
        # Create migration files for both databases
        for db_type in ["core", "docs"]:
            migrations_dir = Path(__file__).parent / "migrations" / db_type
            # Find next migration number
            existing_files = list(migrations_dir.glob("*.up.sql"))
            next_num = len(existing_files) + 1
            
            up_file = migrations_dir / f"{next_num:03d}_{migration_name}.up.sql"
            down_file = migrations_dir / f"{next_num:03d}_{migration_name}.down.sql"
            
            up_file.write_text(f"-- Migration: {migration_name}\n-- Add your up migration SQL here\n")
            down_file.write_text(f"-- Migration: {migration_name}\n-- Add your down migration SQL here\n")
            
            print(f"Created {up_file}")
            print(f"Created {down_file}")
        
        return
    
    # Parse numeric arguments
    numeric_args = []
    for arg in args:
        try:
            numeric_args.append(int(arg))
        except ValueError:
            print(f"Invalid numeric argument: {arg}")
            sys.exit(1)
    
    # Run migration on both databases
    print("=== Migrating Core Database ===")
    core_runner = get_core_runner()
    
    if command == "up":
        core_result = core_runner.up(numeric_args[0] if numeric_args else None)
    elif command == "down":
        core_result = core_runner.down(numeric_args[0] if numeric_args else None)
    elif command == "goto":
        if not numeric_args:
            print("Usage: python migrate.py goto <version>")
            sys.exit(1)
        core_result = core_runner.goto(numeric_args[0])
    elif command == "force":
        if not numeric_args:
            print("Usage: python migrate.py force <version>")
            sys.exit(1)
        core_result = core_runner.force(numeric_args[0])
    elif command == "version":
        core_result = core_runner.version()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    print("\n=== Migrating Docs Database ===")
    docs_runner = get_docs_runner()
    
    if command == "up":
        docs_result = docs_runner.up(numeric_args[0] if numeric_args else None)
    elif command == "down":
        docs_result = docs_runner.down(numeric_args[0] if numeric_args else None)
    elif command == "goto":
        docs_result = docs_runner.goto(numeric_args[0])
    elif command == "force":
        docs_result = docs_runner.force(numeric_args[0])
    elif command == "version":
        docs_result = docs_runner.version()
    else:
        docs_result = 0  # Should not reach here
    
    # Exit with error if any migration failed
    if core_result != 0 or docs_result != 0:
        print(f"\nMigration failed! Core: {core_result}, Docs: {docs_result}")
        sys.exit(1)
    else:
        print("\nMigrations completed successfully!")

if __name__ == "__main__":
    main()