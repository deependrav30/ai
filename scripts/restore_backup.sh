#!/bin/bash

# Restore Script for AI Agent System
# Restores from timestamped backup

if [ -z "$1" ]; then
    echo "Usage: ./restore_backup.sh <timestamp>"
    echo "Example: ./restore_backup.sh 20260201_020000"
    echo ""
    echo "Available backups:"
    ls -1 backups/ | grep postgres | sed 's/postgres_/  /' | sed 's/.sql.gz//'
    exit 1
fi

TIMESTAMP=$1
BACKUP_DIR="backups"

echo "🔄 AI Agent System Restore"
echo "=========================="
echo "Restoring from: $TIMESTAMP"
echo ""

# Verify backups exist
if [ ! -f "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz" ]; then
    echo "✗ PostgreSQL backup not found"
    exit 1
fi

if [ ! -f "$BACKUP_DIR/chromadb_$TIMESTAMP.tar.gz" ]; then
    echo "✗ ChromaDB backup not found"
    exit 1
fi

# Confirm restore
read -p "⚠️  This will overwrite current data. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop services
echo "🛑 Stopping services..."
docker compose down

# Restore PostgreSQL
echo "📦 Restoring PostgreSQL..."
gunzip < "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz" | docker exec -i ai_postgres psql -U ai_agent -d episodic_memory
if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL restored"
else
    echo "✗ PostgreSQL restore failed"
    exit 1
fi

# Restore ChromaDB
echo "📦 Restoring ChromaDB..."
tar -xzf "$BACKUP_DIR/chromadb_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR"
docker cp "$BACKUP_DIR/chromadb_$TIMESTAMP" ai_chromadb:/chroma/chroma
rm -rf "$BACKUP_DIR/chromadb_$TIMESTAMP"
if [ $? -eq 0 ]; then
    echo "✓ ChromaDB restored"
else
    echo "✗ ChromaDB restore failed"
    exit 1
fi

# Restore Redis
if [ -f "$BACKUP_DIR/redis_$TIMESTAMP.rdb.gz" ]; then
    echo "📦 Restoring Redis..."
    gunzip -c "$BACKUP_DIR/redis_$TIMESTAMP.rdb.gz" > "$BACKUP_DIR/redis_temp.rdb"
    docker cp "$BACKUP_DIR/redis_temp.rdb" ai_redis:/data/dump.rdb
    rm "$BACKUP_DIR/redis_temp.rdb"
    echo "✓ Redis restored"
fi

# Restart services
echo "🚀 Restarting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run health check
./scripts/health_check.sh

echo ""
echo "✅ Restore completed"
echo "Verify data integrity and test functionality"
