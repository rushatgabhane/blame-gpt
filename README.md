## Why is my shiny new feature not on production yet?

Oh... we have deploy blockers!!

This tool finds the pull requests begging to be reverted so you can go back to shipping.


(Blame the PR, not your coworker. Probably.)


## Database Migrations

This project uses a database migration system for schema management. See [MIGRATIONS.md](MIGRATIONS.md) for detailed documentation.

Quick start:
```bash
# Run all pending migrations
./db-migrate.sh up

# Check migration status  
./db-migrate.sh status

# Create new migration
./db-migrate.sh create migration_name
```

## Finding the PR causing a deploy blocker
<img src="https://github.com/user-attachments/assets/c049bc22-b194-45ef-b2c7-1e58bd6a999b" height=500>
