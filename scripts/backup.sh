#!/bin/bash

# Backup Script for AI Agent System
# Creates timestamped backups of all data stores

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔄 AI Agent System Backup"
echo "========================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
echo "📦 Backing up PostgreSQL..."
docker exec ai_postgres pg_dump -U ai_agent episodic_memory | gzip > "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"
if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz" | cut -f1)
    echo "✓ PostgreSQL backup complete ($SIZE)"
else
    echo "✗ PostgreSQL backup failed"
    exit 1
fi

# Backup ChromaDB
echo "📦 Backing up ChromaDB..."
docker cp ai_chromadb:/chroma/chroma "$BACKUP_DIR/chromadb_$TIMESTAMP"
if [ $? -eq 0 ]; then
    tar -czf "$BACKUP_DIR/chromadb_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "chromadb_$TIMESTAMP"
    rm -rf "$BACKUP_DIR/chromadb_$TIMESTAMP"
    SIZE=$(du -h "$BACKUP_DIR/chromadb_$TIMESTAMP.tar.gz" | cut -f1)
    echo "✓ ChromaDB backup complete ($SIZE)"
else
    echo "✗ ChromaDB backup failed"
    exit 1
fi

# Backup Redis (if persistence enabled)
echo "📦 Backing up Redis..."
docker exec ai_redis redis-cli BGSAVE
sleep 2  # Wait for background save
docker cp ai_redis:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"
if [ $? -eq 0 ]; then
    gzip "$BACKUP_DIR/redis_$TIMESTAMP.rdb"
    SIZE=$(du -h "$BACKUP_DIR/redis_$TIMESTAMP.rdb.gz" | cut -f1)
    echo "✓ Redis backup complete ($SIZE)"
else
    echo "✗ Redis backup failed"
    exit 1
fi

# Backup configuration files
echo "📦 Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
    docker-compose.yml \
    docker/ \
    .env 2>/dev/null || true

SIZE=$(du -h "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" | cut -f1)
echo "✓ Configuration backup complete ($SIZE)"

# Cleanup old backups (keep last 7 days)
echo ""
echo "🧹 Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete

echo ""
echo "✅ Backup completed successfully"
echo "Backup location: $BACKUP_DIR/"
echo ""

# List recent backups
echo "Recent backups:"
ls -lh "$BACKUP_DIR" | tail -10
