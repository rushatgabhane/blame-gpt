# Database Migrations

This project uses a golang-migrate-compatible migration system for database schema management.

## Quick Start

### Run Migrations
```bash
# Run all pending migrations
./db-migrate.sh up

# Or use Python directly
python migrate.py up
```

### Check Migration Status
```bash
# Check current migration version
./db-migrate.sh status
```

### Create New Migration
```bash
# Create new migration files
./db-migrate.sh create add_user_table
```

## Migration Commands

### Using the Shell Script (Recommended)
```bash
./db-migrate.sh up           # Run all pending migrations
./db-migrate.sh down         # Rollback 1 migration  
./db-migrate.sh down 3       # Rollback 3 migrations
./db-migrate.sh status       # Show current version
./db-migrate.sh create <name> # Create new migration
./db-migrate.sh reset        # Reset database completely
```

### Using Python Directly
```bash
python migrate.py up [N]        # Run all or N migrations up
python migrate.py down [N]      # Run all or N migrations down
python migrate.py goto VERSION  # Migrate to specific version
python migrate.py force VERSION # Force set version
python migrate.py version       # Show current version
python migrate.py create NAME   # Create new migration files
```

## File Structure

```
migrations/
├── core/                    # Core database migrations
│   ├── 001_initial_tables.up.sql
│   ├── 001_initial_tables.down.sql
│   └── ...
└── docs/                    # Docs database migrations
    ├── 001_initial_tables.up.sql
    ├── 001_initial_tables.down.sql
    └── ...
```

## Migration File Format

- **Up migrations**: `NNN_description.up.sql` (e.g., `001_initial_tables.up.sql`)
- **Down migrations**: `NNN_description.down.sql` (e.g., `001_initial_tables.down.sql`)

Where `NNN` is a 3-digit version number.

## Creating New Migrations

1. Create new migration files:
   ```bash
   ./db-migrate.sh create add_new_column
   ```

2. Edit the generated `.up.sql` file with your schema changes:
   ```sql
   -- Migration: add_new_column
   ALTER TABLE users ADD COLUMN email TEXT;
   ```

3. Edit the corresponding `.down.sql` file with the rollback:
   ```sql
   -- Migration: add_new_column
   ALTER TABLE users DROP COLUMN email;
   ```

4. Run the migration:
   ```bash
   ./db-migrate.sh up
   ```

## Database Schema Versioning

The migration system automatically tracks schema versions using a `schema_migrations` table in each database. This table stores:
- `version`: The migration version number
- `dirty`: Whether the migration failed (for error recovery)

## Compatibility with Existing Code

The migration system is designed to work alongside existing database initialization code:

- If migrations have been run (schema_migrations table exists), the app uses the migrated schema
- If no migrations have been run, the app falls back to the original table creation method
- This ensures backward compatibility and smooth transitions

## Production Deployment

1. **Always run migrations before deploying application code**:
   ```bash
   ./db-migrate.sh up
   ```

2. **Test migrations on a database copy first**:
   ```bash
   # Copy production database
   cp data/cache.db data/cache_backup.db
   
   # Test migration
   ./db-migrate.sh up
   
   # If something goes wrong, restore backup
   cp data/cache_backup.db data/cache.db
   ```

3. **For rollbacks in production**:
   ```bash
   # Check what version you want to rollback to
   ./db-migrate.sh status
   
   # Rollback specific number of migrations
   ./db-migrate.sh down 2
   ```

## Best Practices

1. **Always create both up and down migrations**
2. **Test migrations locally before deployment**
3. **Keep migrations small and focused**
4. **Never edit existing migration files after they've been applied**
5. **Use descriptive names for migrations**
6. **Backup databases before running migrations in production**

## Troubleshooting

### Migration Failed (Dirty State)
If a migration fails, the database might be in a "dirty" state:

```bash
# Check status
./db-migrate.sh status

# Fix manually and force version
python migrate.py force <correct_version>
```

### Reset Everything
To start fresh (⚠️ **This deletes all data**):

```bash
./db-migrate.sh reset
```

### Manual Database Inspection
```bash
# Connect to database
sqlite3 data/cache.db

# Check migration status
SELECT * FROM schema_migrations;

# List all tables
.tables

# Exit
.quit
```