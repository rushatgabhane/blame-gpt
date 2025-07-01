#!/bin/bash
# Database migration helper script

case "$1" in
    "up")
        echo "Running all pending migrations..."
        python migrate.py up
        ;;
    "down")
        if [ -z "$2" ]; then
            echo "Running one migration down..."
            python migrate.py down 1
        else
            echo "Running $2 migrations down..."
            python migrate.py down "$2"
        fi
        ;;
    "status"|"version")
        echo "Checking migration status..."
        python migrate.py version
        ;;
    "create")
        if [ -z "$2" ]; then
            echo "Usage: $0 create <migration_name>"
            exit 1
        fi
        echo "Creating new migration: $2"
        python migrate.py create "$2"
        ;;
    "reset")
        echo "WARNING: This will reset the database!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f data/cache.db data/docs.db
            python migrate.py up
            echo "Database reset complete!"
        else
            echo "Reset cancelled."
        fi
        ;;
    *)
        echo "Usage: $0 {up|down [N]|status|create <name>|reset}"
        echo ""
        echo "Commands:"
        echo "  up           - Run all pending migrations"
        echo "  down [N]     - Run N migrations down (default: 1)"
        echo "  status       - Show current migration version"
        echo "  create <name> - Create new migration files"
        echo "  reset        - Reset database and run all migrations"
        echo ""
        echo "Examples:"
        echo "  $0 up                    # Run all pending migrations"
        echo "  $0 down                  # Rollback 1 migration"
        echo "  $0 down 3                # Rollback 3 migrations" 
        echo "  $0 create add_new_field  # Create new migration files"
        echo "  $0 status                # Check current version"
        exit 1
        ;;
esac