#!/bin/bash

# Railway Database Cleanup Deployment Script
# Removes financial tables and ensures only knowledge_base is used

echo "======================================"
echo "🚀 RAILWAY DATABASE CLEANUP DEPLOYMENT"
echo "======================================"
echo "Date: $(date)"
echo ""

# Step 1: Backup current models.py
echo "📦 Step 1: Backing up current files..."
cp src/db/models.py src/db/models_backup.py
cp src/db/connection.py src/db/connection_backup.py
cp src/tools/connectors/sql.py src/tools/connectors/sql_backup.py
echo "✅ Backups created"

# Step 2: Replace with clean versions
echo ""
echo "📝 Step 2: Updating to clean versions..."
cp src/db/models_clean.py src/db/models.py
cp src/db/postgres_connection.py src/db/connection.py
cp src/tools/connectors/sql_clean.py src/tools/connectors/sql.py
echo "✅ Files updated"

# Step 3: Commit changes
echo ""
echo "💾 Step 3: Committing changes..."
git add src/db/models.py src/db/connection.py src/tools/connectors/sql.py
git add src/db/models_clean.py src/db/postgres_connection.py src/tools/connectors/sql_clean.py
git add scripts/cleanup_database.py scripts/deploy_cleanup.sh

git commit -m "Remove financial tables and SQLite dependencies

- Replaced models.py with knowledge_base only schema
- Updated connection.py to use PostgreSQL exclusively  
- Cleaned SQL tool to only query knowledge_base table
- Removed all references to financial/company tables
- Removed SQLite dependencies

This ensures the system only uses the knowledge_base table
and PostgreSQL for Railway deployment.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Changes committed"

# Step 4: Push to Railway
echo ""
echo "🚂 Step 4: Pushing to Railway..."
git push origin main

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Wait for Railway to deploy the changes"
echo "2. Run: python scripts/cleanup_database.py (to drop financial tables)"
echo "3. Monitor Railway logs for any errors"
echo "4. Test the /query endpoint to verify it works"
echo ""
echo "⚠️  IMPORTANT: The cleanup_database.py script will DROP these tables:"
echo "  - companies"
echo "  - financial_records"
echo "  - financial_data"
echo "  - accounts"
echo "  - transactions"
echo "  - portfolios"
echo "  - debt_accounts"
echo "  - benchmarks"
echo ""
echo "Only the knowledge_base table will remain."